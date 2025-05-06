from typing import List, Tuple, Optional

from github_stats.api.client import GitHubClient, APIError
from github_stats.api.queries import REPO_LOC_QUERY
from github_stats.config import config


def process_loc_for_repo(
        owner: str,
        repo_name: str,
        data: List[str],
        cache_comment: List[str],
        cursor: Optional[str] = None,
        addition_total: int = 0,
        deletion_total: int = 0,
        my_commits: int = 0
) -> Tuple[int, int, int]:
    """
    Process lines of code for a specific repository.

    Args:
        owner: Repository owner
        repo_name: Repository name
        data: Cache data
        cache_comment: Cache comments
        cursor: Pagination cursor
        addition_total: Current count of additions
        deletion_total: Current count of deletions
        my_commits: Current count of commits

    Returns:
        Tuple of (additions, deletions, commit count)
    """
    try:
        response = GitHubClient.execute_query(
            'recursive_loc',
            REPO_LOC_QUERY,
            {'repo_name': repo_name, 'owner': owner, 'cursor': cursor}
        )

        repo_data = response['data']['repository']
        if repo_data['defaultBranchRef'] is None:
            return addition_total, deletion_total, my_commits

        history = repo_data['defaultBranchRef']['target']['history']

        # Count lines of code and commits
        for node in history['edges']:
            if node['node']['author']['user'] == config.owner_id:
                my_commits += 1
                addition_total += node['node']['additions']
                deletion_total += node['node']['deletions']

        # Handle pagination if there are more commits
        if history['edges'] and history['pageInfo']['hasNextPage']:
            # Import here to avoid circular imports
            from github_stats.cache.manager import CacheManager

            return process_loc_for_repo(
                owner, repo_name, data, cache_comment,
                history['pageInfo']['endCursor'],
                addition_total, deletion_total, my_commits
            )

        return addition_total, deletion_total, my_commits

    except APIError as e:
        # Import here to avoid circular imports
        from github_stats.cache.manager import CacheManager

        # Save what we have before failing
        CacheManager.force_close_file(data, cache_comment)
        raise e