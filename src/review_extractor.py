from typing import List, Dict, Any

class ReviewExtractor:
    @staticmethod
    def extract_reviews(raw_repo_data: List[Dict]) -> List[Dict]:
        extracted = []
        for pr_data in raw_repo_data:
            repo_name = pr_data['repo_name']
            pr_number = pr_data['pr_number']
            full_diff = pr_data['diff']
            
            for comment in pr_data['comments']:
                if 'diff_hunk' in comment and comment['diff_hunk']:
                    extracted.append({
                        "repository": {"repo_name": repo_name, "repository_url": f"https://github.com/{repo_name}"},
                        "pull_request": {"pr_number": str(pr_number), "pr_url": pr_data['pr_url']},
                        "file": {"file_path": comment.get('path', ''), "file_extension": "", "programming_language": ""},
                        "review": {
                            "review_id": str(comment['id']),
                            "reviewer": comment['user']['login'] if comment.get('user') else "",
                            "is_bot": comment['user'].get('type') == 'Bot' if comment.get('user') else False,
                            "created_at": comment.get('created_at', ''),
                            "updated_at": comment.get('updated_at', ''),
                            "line_number": str(comment.get('line', '')),
                            "code_diff": comment['diff_hunk'],
                            "review_comment": comment['body'],
                            "comment_length": str(len(comment['body']))
                        },
                        "metadata": {"quality_score": "", "token_count": "", "dataset_version": "v1.0.0", "source": "github_api"},
                        "annotations": {
                            "review_type": "inline",
                            "issue_type": None,
                            "severity": None,
                            "confidence_score": None,
                            "suggested_fix": None,
                            "tags": []
                        }
                    })
        return extracted
