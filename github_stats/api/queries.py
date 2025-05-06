"""GraphQL queries for GitHub API interactions."""

USER_QUERY = '''
query($login: String!){
    user(login: $login) {
        id
        createdAt
    }
}'''

FOLLOWER_QUERY = '''
query($login: String!){
    user(login: $login) {
        followers {
            totalCount
        }
    }
}'''

REPOS_STARS_QUERY = '''
query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
    user(login: $login) {
        repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
            totalCount
            edges {
                node {
                    ... on Repository {
                        nameWithOwner
                        stargazers {
                            totalCount
                        }
                    }
                }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}'''

COMMITS_QUERY = '''
query($start_date: DateTime!, $end_date: DateTime!, $login: String!) {
    user(login: $login) {
        contributionsCollection(from: $start_date, to: $end_date) {
            contributionCalendar {
                totalContributions
            }
        }
    }
}'''

LOC_QUERY = '''
query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
    user(login: $login) {
        repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
        edges {
            node {
                ... on Repository {
                    nameWithOwner
                    defaultBranchRef {
                        target {
                            ... on Commit {
                                history {
                                    totalCount
                                    }
                                }
                            }
                        }
                    }
                }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}'''

REPO_LOC_QUERY = '''
query ($repo_name: String!, $owner: String!, $cursor: String) {
    repository(name: $repo_name, owner: $owner) {
        defaultBranchRef {
            target {
                ... on Commit {
                    history(first: 100, after: $cursor) {
                        totalCount
                        edges {
                            node {
                                ... on Commit {
                                    committedDate
                                }
                                author {
                                    user {
                                        id
                                    }
                                }
                                deletions
                                additions
                            }
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
        }
    }
}'''