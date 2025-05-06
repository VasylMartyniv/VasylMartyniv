import hashlib
import os
from typing import List, Dict, Any

from github_stats.api.repo_processing import process_loc_for_repo
from github_stats.config import config


class CacheManager:
    """Manages caching of repository data to avoid repeated API calls."""

    def __init__(self, user_name: str):
        """
        Initialize cache manager.

        Args:
            user_name: GitHub username to create cache for
        """
        self.user_name = user_name
        self.cache_dir = 'cache'
        self._ensure_cache_dir()
        self.cache_file = self._get_cache_filename()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_filename(self) -> str:
        """Get the cache filename based on username hash."""
        username_hash = hashlib.sha256(self.user_name.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{username_hash}.txt")

    def cache_builder(
            self,
            edges: List[Dict[str, Any]],
            comment_size: int,
            force_cache: bool,
            loc_add: int = 0,
            loc_del: int = 0
    ) -> List[int]:
        """
        Build or update cache for repository data.

        Args:
            edges: Repository edges from GraphQL query
            comment_size: Number of comment lines at the start of cache file
            force_cache: Whether to force rebuild the cache
            loc_add: Initial lines added count
            loc_del: Initial lines deleted count

        Returns:
            List containing [loc_add, loc_del, loc_diff, is_cached]
        """
        cached = True

        # Try to read existing cache file
        try:
            with open(self.cache_file, 'r') as f:
                data = f.readlines()
        except FileNotFoundError:
            data = []
            if comment_size > 0:
                for _ in range(comment_size):
                    data.append('This line is a comment block. Write whatever you want here.\n')
            with open(self.cache_file, 'w') as f:
                f.writelines(data)

        # Check if cache needs rebuilding
        if len(data) - comment_size != len(edges) or force_cache:
            cached = False
            self._flush_cache(edges, comment_size)
            with open(self.cache_file, 'r') as f:
                data = f.readlines()

        cache_comment = data[:comment_size]
        data = data[comment_size:]

        # Process each repository
        for index in range(len(edges)):
            repo_hash, commit_count, *__ = data[index].split()
            repo_hash_calculated = hashlib.sha256(
                edges[index]['node']['nameWithOwner'].encode('utf-8')
            ).hexdigest()

            if repo_hash == repo_hash_calculated:
                try:
                    current_commit_count = edges[index]['node']['defaultBranchRef']['target']['history']['totalCount']
                    if int(commit_count) != current_commit_count:
                        # Repository needs updating
                        owner, repo_name = edges[index]['node']['nameWithOwner'].split('/')
                        loc = process_loc_for_repo(owner, repo_name, data, cache_comment)
                        data[index] = f"{repo_hash} {current_commit_count} {loc[2]} {loc[0]} {loc[1]}\n"
                except TypeError:
                    data[index] = f"{repo_hash} 0 0 0 0\n"

        # Save updated cache
        with open(self.cache_file, 'w') as f:
            f.writelines(cache_comment)
            f.writelines(data)

        # Calculate totals
        for line in data:
            loc = line.split()
            loc_add += int(loc[3])
            loc_del += int(loc[4])

        return [loc_add, loc_del, loc_add - loc_del, cached]

    def _flush_cache(self, edges: List[Dict[str, Any]], comment_size: int) -> None:
        """
        Wipe and recreate cache file.

        Args:
            edges: Repository edges to create cache entries for
            comment_size: Number of comment lines to preserve
        """
        # Read existing comments if any
        data = []
        try:
            with open(self.cache_file, 'r') as f:
                if comment_size > 0:
                    data = f.readlines()[:comment_size]
        except FileNotFoundError:
            # Add default comments if file doesn't exist
            if comment_size > 0:
                for _ in range(comment_size):
                    data.append('This line is a comment block. Write whatever you want here.\n')

        # Write new empty cache entries
        with open(self.cache_file, 'w') as f:
            f.writelines(data)
            for node in edges:
                repo_hash = hashlib.sha256(node['node']['nameWithOwner'].encode('utf-8')).hexdigest()
                f.write(f"{repo_hash} 0 0 0 0\n")

    @staticmethod
    def add_archive() -> List[int]:
        """
        Add archived repository data to calculations.

        Returns:
            List containing [added_loc, deleted_loc, net_loc, commits, repos]
        """
        try:
            with open('cache/repository_archive.txt', 'r') as f:
                data = f.readlines()

            # Parse archived data
            old_data = data
            data = data[7:len(data) - 3]
            added_loc, deleted_loc, added_commits = 0, 0, 0
            contributed_repos = len(data)

            for line in data:
                repo_hash, total_commits, my_commits, *loc = line.split()
                added_loc += int(loc[0])
                deleted_loc += int(loc[1])
                if my_commits.isdigit():
                    added_commits += int(my_commits)

            # Add additional commits from the last line (special case)
            added_commits += int(old_data[-1].split()[4][:-1])

            return [
                added_loc,
                deleted_loc,
                added_loc - deleted_loc,
                added_commits,
                contributed_repos
            ]
        except (FileNotFoundError, IndexError):
            return [0, 0, 0, 0, 0]

    @classmethod
    def force_close_file(cls, data: List[str], cache_comment: List[str]) -> None:
        """
        Force close cache file with partial data in case of errors.

        Args:
            data: Current cache data
            cache_comment: Comment section of cache file
        """
        cache_file = os.path.join(
            'cache',
            f"{hashlib.sha256(config.user_name.encode('utf-8')).hexdigest()}.txt"
        )
        with open(cache_file, 'w') as f:
            f.writelines(cache_comment)
            f.writelines(data)
        print(f'There was an error while writing to the cache file. The file, {cache_file} has had the partial data saved and closed.')