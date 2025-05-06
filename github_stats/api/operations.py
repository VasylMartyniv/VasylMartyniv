from typing import Any, Dict, List, Optional, Tuple

from github_stats.api.client import GitHubClient
from github_stats.api.queries import (
    USER_QUERY, FOLLOWER_QUERY, REPOS_STARS_QUERY,
    COMMITS_QUERY, LOC_QUERY
)
from github_stats.cache.manager import CacheManager
from github_stats.config import config


def get_user_info(username: str) -> Tuple[Dict[str, str], str]:
    """
    Returns the account ID and creation time of the user.

    Args:
        username: GitHub username

    Returns:
        Tuple containing user ID and creation time
    """
    response = GitHubClient.execute_query(
        'user_getter',
        USER_QUERY,
        {'login': username}
    )
    return (
        {'id': response['data']['user']['id']},
        response['data']['user']['createdAt']
    )


def get_follower_count(username: str) -> int:
    """
    Returns the number of followers of the user.

    Args:
        username: GitHub username

    Returns:
        The number of followers
    """
    response = GitHubClient.execute_query(
        'follower_getter',
        FOLLOWER_QUERY,
        {'login': username}
    )
    return int(response['data']['user']['followers']['totalCount'])


def count_stars_from_edges(edges: List[Dict[str, Any]]) -> int:
    """
    Count total stars in repositories.

    Args:
        edges: Repository edges from GraphQL response

    Returns:
        Total star count
    """
    total_stars = 0
    for node in edges:
        total_stars += node['node']['stargazers']['totalCount']
    return total_stars


def get_repos_or_stars(
        count_type: str,
        owner_affiliation: List[str],
        cursor: Optional[str] = None
) -> int:
    """
    Get repository or star count for a user based on affiliation.

    Args:
        count_type: 'repos' or 'stars' depending on what to count
        owner_affiliation: List of repository affiliations to include
        cursor: Pagination cursor

    Returns:
        Count of repositories or stars
    """
    response = GitHubClient.execute_query(
        'graph_repos_stars',
        REPOS_STARS_QUERY,
        {
            'owner_affiliation': owner_affiliation,
            'login': config.user_name,
            'cursor': cursor
        }
    )

    if count_type == 'repos':
        return response['data']['user']['repositories']['totalCount']
    elif count_type == 'stars':
        return count_stars_from_edges(response['data']['user']['repositories']['edges'])

    return 0


def get_commit_count(start_date: str, end_date: str) -> int:
    """
    Get commit count for a date range.

    Args:
        start_date: ISO format start date
        end_date: ISO format end date

    Returns:
        Count of commits in the given time period
    """
    response = GitHubClient.execute_query(
        'graph_commits',
        COMMITS_QUERY,
        {
            'start_date': start_date,
            'end_date': end_date,
            'login': config.user_name
        }
    )
    return int(response['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])


def get_loc_statistics(
        owner_affiliation: List[str],
        comment_size: int = 0,
        force_cache: bool = False,
        cursor: Optional[str] = None,
        edges: List[Dict[str, Any]] = None
) -> List[int]:
    """
    Get lines of code statistics across all repositories with given affiliation.

    Args:
        owner_affiliation: List of repository affiliations to include
        comment_size: Size of comment section in cache file
        force_cache: Whether to force cache rebuild
        cursor: Pagination cursor
        edges: Repository edges collected so far

    Returns:
        List containing [loc_add, loc_del, loc_total, is_cached]
    """
    if edges is None:
        edges = []

    response = GitHubClient.execute_query(
        'loc_query',
        LOC_QUERY,
        {
            'owner_affiliation': owner_affiliation,
            'login': config.user_name,
            'cursor': cursor
        }
    )

    page_info = response['data']['user']['repositories']['pageInfo']
    current_edges = response['data']['user']['repositories']['edges']

    # If repository data has another page
    if page_info['hasNextPage']:
        # Recursively get the rest of the edges
        return get_loc_statistics(
            owner_affiliation,
            comment_size,
            force_cache,
            page_info['endCursor'],
            edges + current_edges
        )
    else:
        # Process all collected edges
        cache_manager = CacheManager(config.user_name)
        return cache_manager.cache_builder(
            edges + current_edges,
            comment_size,
            force_cache
        )