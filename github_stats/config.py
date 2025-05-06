import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Config:
    """Application configuration settings."""

    user_name: str
    access_token: str
    headers: Dict[str, str] = field(default_factory=dict)
    owner_id: Optional[Dict[str, str]] = None
    query_count: Dict[str, int] = field(default_factory=lambda: {
        'user_getter': 0,
        'follower_getter': 0,
        'graph_repos_stars': 0,
        'recursive_loc': 0,
        'graph_commits': 0,
        'loc_query': 0
    })

    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        user_name = os.getenv('USER_NAME')
        access_token = os.getenv('ACCESS_TOKEN')

        if not user_name:
            raise ValueError("USER_NAME environment variable is required")

        if not access_token:
            raise ValueError("ACCESS_TOKEN environment variable is required")

        headers = {'authorization': f'token {access_token}'}

        return cls(
            user_name=user_name,
            access_token=access_token,
            headers=headers
        )

    def increment_query_count(self, query_name: str) -> None:
        """Increment the count for a specific query type."""
        if query_name in self.query_count:
            self.query_count[query_name] += 1


# Create global configuration instance
config = Config.from_env()