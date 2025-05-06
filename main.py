import datetime

from github_stats.api.operations import (
    get_user_info, get_follower_count, get_repos_or_stars,
    get_commit_count, get_loc_statistics
)
from github_stats.cache.manager import CacheManager
from github_stats.config import config
from github_stats.export.svg import format_age_string, count_commit_stats, update_svg
from github_stats.utils.performance import measure_performance, format_execution_time


def main() -> None:
    """Main entry point for the GitHub stats application."""
    print('Calculation times:')

    # Get user data
    (user_data, account_date), user_time = measure_performance(get_user_info, config.user_name)
    config.owner_id = user_data
    format_execution_time('account data', user_time)

    # Calculate age data
    birthday = datetime.datetime(1999, 8, 18)  # This should be configurable
    age_data, age_time = measure_performance(format_age_string, birthday)
    format_execution_time('age calculation', age_time)

    # Get lines of code statistics
    total_loc, loc_time = measure_performance(
        get_loc_statistics,
        ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'],
        7  # Comment size
    )

    # Show appropriate message based on cache status
    if total_loc[-1]:
        format_execution_time('LOC (cached)', loc_time)
    else:
        format_execution_time('LOC (no cache)', loc_time)

    # Get other statistics
    commit_data, commit_time = measure_performance(count_commit_stats, 7)
    star_data, star_time = measure_performance(get_repos_or_stars, 'stars', ['OWNER'])
    repo_data, repo_time = measure_performance(get_repos_or_stars, 'repos', ['OWNER'])
    contrib_data, contrib_time = measure_performance(
        get_repos_or_stars,
        'repos',
        ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER']
    )
    follower_data, follower_time = measure_performance(get_follower_count, config.user_name)

    # Add archived repository data if this is the original user
    if config.owner_id == {'id': 'MDQ6VXNlcjE2NjY4MTc1'}:
        archived_data = CacheManager.add_archive()
        for index in range(len(total_loc) - 1):
            total_loc[index] += archived_data[index]
        contrib_data += archived_data[-1]
        commit_data += int(archived_data[-2])

    # Format LOC data for display
    formatted_loc = []
    for index in range(len(total_loc) - 1):
        formatted_loc.append('{:,}'.format(total_loc[index]))

    # Update SVG files
    update_svg(
        'dark_mode.svg',
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        formatted_loc
    )
    update_svg(
        'light_mode.svg',
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        formatted_loc
    )

    # Display performance summary
    total_time = user_time + age_time + loc_time + commit_time + star_time + repo_time + contrib_time

    # Move cursor up to overwrite previous lines (ANSI escape code)
    print(
        '\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F',
        '{:<21}'.format('Total function time:'),
        '{:>11}'.format('%.4f' % total_time),
        ' s \033[E\033[E\033[E\033[E\033[E\033[E\033[E\033[E',
        sep=''
    )

    # Print API call statistics
    print(f"Total GitHub GraphQL API calls: {sum(config.query_count.values()):>3}")
    for query_name, count in config.query_count.items():
        print(f"   {query_name:<24} {count:>6}")


if __name__ == '__main__':
    main()