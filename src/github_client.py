import os
import requests
import time
import logging
import yaml
from typing import Optional, Dict, Any, List

class GitHubClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GitHubClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.tokens = []
        config_path = os.path.join("config", "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                # Check for list of tokens or single token
                if "github_tokens" in config and isinstance(config["github_tokens"], list):
                    self.tokens = config["github_tokens"]
                elif "github_token" in config and config["github_token"]:
                    self.tokens = [config["github_token"]]
                    
        # Check env fallback
        env_token = os.environ.get("GITHUB_TOKEN")
        if env_token and env_token not in self.tokens:
            self.tokens.append(env_token)
            
        if not self.tokens:
            raise ValueError("No GitHub tokens found. Set 'github_tokens' as a list in config/config.yaml.")
            
        self.current_token_index = 0
        
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self._apply_current_token()

    def _apply_current_token(self):
        token = self.tokens[self.current_token_index]
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })

    def _rotate_token(self):
        self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
        self._apply_current_token()
        self.logger.info(f"Swapped to API token {self.current_token_index + 1}/{len(self.tokens)}")

    def _handle_rate_limit(self, response: requests.Response, attempt: int = 1):
        if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
            if response.headers["X-RateLimit-Remaining"] == "0":
                if attempt < len(self.tokens):
                    self.logger.warning(f"Token {self.current_token_index + 1} rate limited. Rotating to next token...")
                    self._rotate_token()
                    return True # Retry immediately with new token
                
                # If we've exhausted all tokens, we have to sleep based on the current one
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 3600))
                sleep_time = reset_time - int(time.time()) + 1
                self.logger.warning(f"ALL tokens rate limited. Sleeping for {sleep_time} seconds.")
                time.sleep(max(1, sleep_time))
                # After sleeping, reset attempt count because tokens are fresh
                return True 
        return False

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        attempt = 1
        while True:
            response = self.session.get(url, params=params)
            is_rate_limited = (response.status_code == 403 and "X-RateLimit-Remaining" in response.headers and response.headers["X-RateLimit-Remaining"] == "0")
            
            if self._handle_rate_limit(response, attempt):
                if is_rate_limited:
                    attempt += 1
                continue
            response.raise_for_status()
            return response

    def get_paginated(self, endpoint: str, params: Optional[Dict] = None, max_pages: int = 10) -> List[Dict]:
        results = []
        page = 1
        params = params or {}
        while page <= max_pages:
            params['page'] = page
            params['per_page'] = 100
            response = self.get(endpoint, params=params)
            data = response.json()
            if not data:
                break
            results.extend(data)
            if 'next' not in response.links:
                break
            page += 1
        return results

client = GitHubClient()
