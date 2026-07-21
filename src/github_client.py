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
        self.token = os.environ.get("GITHUB_TOKEN")
        
        if not self.token:
            config_path = os.path.join("config", "config.yaml")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    self.token = config.get("github_token", "")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN not found. Set it in .env or config/config.yaml before running.")
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
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
        
        self.session.headers.update(self.headers)

    def _handle_rate_limit(self, response: requests.Response):
        if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
            if response.headers["X-RateLimit-Remaining"] == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 3600))
                sleep_time = reset_time - int(time.time()) + 1
                self.logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
                time.sleep(max(1, sleep_time))
                return True
        return False

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        while True:
            response = self.session.get(url, params=params)
            if self._handle_rate_limit(response):
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
