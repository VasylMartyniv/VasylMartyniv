from typing import Any, Dict, Optional

import requests

from github_stats.config import config


class APIError(Exception):
    """Exception raised for API errors."""
    pass


class GitHubClient:
    """Client for interacting with GitHub GraphQL API."""

    API_URL = 'https://api.github.com/graphql'

    @classmethod
    def execute_query(
            cls,
            query_name: str,
            query: str,
            variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the GitHub API.

        Args:
            query_name: Name of the query for tracking and error reporting
            query: GraphQL query string
            variables: Variables for the GraphQL query

        Returns:
            The JSON response from the API

        Raises:
            APIError: If the request fails
        """
        # Update query counter
        config.increment_query_count(query_name)

        # Make request
        response = requests.post(
            cls.API_URL,
            json={'query': query, 'variables': variables or {}},
            headers=config.headers
        )

        # Handle response
        if response.status_code == 200:
            return response.json()

        # Handle errors
        if response.status_code == 403:
            raise APIError("Rate limit exceeded. You've hit GitHub's anti-abuse limit.")

        raise APIError(
            f"Query '{query_name}' failed with status {response.status_code}: {response.text}"
        )