import datetime
import hashlib
from typing import List, Union

from dateutil import relativedelta
from lxml import etree

from github_stats.config import config


def format_age_string(birthday: datetime.datetime) -> str:
    """
    Returns a formatted string with time since birthday.

    Args:
        birthday: Birthday datetime object

    Returns:
        Formatted age string (e.g. "23 years, 5 months, 12 days")
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    birthday_emoji = ' 🎂' if (diff.months == 0 and diff.days == 0) else ''

    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, _format_plural('year', diff.years),
        diff.months, _format_plural('month', diff.months),
        diff.days, _format_plural('day', diff.days),
        birthday_emoji
    )


def _format_plural(unit: str, count: int) -> str:
    """
    Add plural 's' to units when needed.

    Args:
        unit: Base unit name
        count: Count of units

    Returns:
        Unit name with pluralization if needed
    """
    return f"{unit}s" if count != 1 else unit


def count_commit_stats(comment_size: int) -> int:
    """
    Count total commits from cache file.

    Args:
        comment_size: Number of comment lines in cache file

    Returns:
        Total commit count
    """
    total_commits = 0
    username_hash = hashlib.sha256(config.user_name.encode('utf-8')).hexdigest()
    cache_file = f"cache/{username_hash}.txt"

    try:
        with open(cache_file, 'r') as f:
            data = f.readlines()

        data = data[comment_size:]
        for line in data:
            total_commits += int(line.split()[2])

        return total_commits
    except (FileNotFoundError, IndexError):
        return 0


def update_svg(
        filename: str,
        age_data: str,
        commit_data: int,
        star_data: int,
        repo_data: int,
        contrib_data: int,
        follower_data: int,
        loc_data: List[str]
) -> None:
    """
    Update SVG file with user statistics.

    Args:
        filename: SVG filename to update
        age_data: Age string
        commit_data: Commit count
        star_data: Star count
        repo_data: Repository count
        contrib_data: Contributed repository count
        follower_data: Follower count
        loc_data: List of [additions, deletions, net] as strings
    """
    tree = etree.parse(filename)
    root = tree.getroot()

    # Update age data
    _find_and_replace(root, 'age_data', age_data)
    age_dots_length = max(0, 49 - len(age_data))
    dot_string = ' ' + ('.' * age_dots_length) + ' ' if age_dots_length > 2 else ' ' if age_dots_length == 1 else ''
    _find_and_replace(root, 'age_data_dots', dot_string)

    # Update other statistics with proper justification
    _justify_format(root, 'commit_data', commit_data, 22)
    _justify_format(root, 'star_data', star_data, 14)
    _justify_format(root, 'repo_data', repo_data, 7)
    _justify_format(root, 'contrib_data', contrib_data)
    _justify_format(root, 'follower_data', follower_data, 10)
    _justify_format(root, 'loc_data', loc_data[2], 9)
    _justify_format(root, 'loc_add', loc_data[0])
    _justify_format(root, 'loc_del', loc_data[1], 7)

    # Write updated SVG
    tree.write(filename, encoding='utf-8', xml_declaration=True)


def _justify_format(root, element_id: str, new_text: Union[int, str], length: int = 0) -> None:
    """
    Update element text and adjust dot justification.

    Args:
        root: XML root element
        element_id: ID of element to update
        new_text: New text content
        length: Target justification length
    """
    if isinstance(new_text, int):
        new_text = f"{'{:,}'.format(new_text)}"
    new_text = str(new_text)

    # Update element text
    _find_and_replace(root, element_id, new_text)

    # Calculate and set dot justification
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_map = {0: '', 1: ' ', 2: '. '}
        dot_string = dot_map[just_len]
    else:
        dot_string = ' ' + ('.' * just_len) + ' '

    _find_and_replace(root, f"{element_id}_dots", dot_string)


def _find_and_replace(root, element_id: str, new_text: str) -> None:
    """
    Find element by ID and update its text.

    Args:
        root: XML root element
        element_id: ID of element to update
        new_text: New text content
    """
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text