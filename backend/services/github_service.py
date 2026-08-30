import httpx
import os
import datetime
from typing import Dict, List


class GitHubService:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.graphql_url = "https://api.github.com/graphql"
        self.rest_url = "https://api.github.com"

    def _get_headers(self):
        if not self.token:
            raise ValueError("GITHUB_TOKEN is not set in .env file")
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def fetch_all(self, username: str) -> Dict:
        try:
            headers = self._get_headers()
        except ValueError as e:
            return {"error": str(e)}

        graphql_query = """
        query($login: String!) {
          user(login: $login) {
            name
            bio
            company
            location
            createdAt
            followers { totalCount }
            following { totalCount }
            repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: PUSHED_AT, direction: DESC}) {
              totalCount
              nodes {
                name
                isFork
                isArchived
                stargazerCount
                forkCount
                primaryLanguage { name }
                languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                  totalSize
                  edges {
                    size
                    node { name }
                  }
                }
                pushedAt
                createdAt
                defaultBranchRef {
                  target {
                    ... on Commit {
                      history(first: 1) {
                        totalCount
                      }
                    }
                  }
                }
              }
            }
            pullRequests(states: MERGED) { totalCount }
            issues(states: OPEN) { totalCount }
            contributionsCollection {
              totalCommitContributions
              totalPullRequestContributions
              totalIssueContributions
              totalRepositoryContributions
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    contributionCount
                    date
                  }
                }
              }
            }
          }
        }
        """

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(
                    self.graphql_url,
                    json={"query": graphql_query, "variables": {"login": username}},
                    headers=headers
                )
            except httpx.TimeoutException:
                return {"error": "GitHub API timed out. Please try again."}
            except httpx.RequestError as e:
                return {"error": f"Network error: {str(e)}"}

            if res.status_code == 401:
                return {"error": "Invalid GitHub Token. Check your .env file."}
            if res.status_code != 200:
                return {"error": f"GitHub API returned status {res.status_code}"}

            response_json = res.json()

            if "errors" in response_json:
                errors = response_json["errors"]
                if any("Could not resolve" in e.get("message", "") for e in errors):
                    return {"error": f"GitHub user '{username}' not found"}
                return {"error": f"GitHub API Error: {errors[0].get('message', 'Unknown')}"}

            user_data = response_json.get("data", {}).get("user")
            if not user_data:
                return {"error": f"GitHub user '{username}' not found"}

            return self._process(user_data, username)

    def _process(self, data: Dict, username: str) -> Dict:
        repos = data["repositories"]["nodes"]

        # Filter out forks and archived repos for quality metrics
        original_repos = [r for r in repos if not r["isFork"] and not r["isArchived"]]
        active_repos = [
            r for r in original_repos
            if r.get("pushedAt") and self._is_recent(r["pushedAt"], days=365)
        ]

        # Language analysis
        lang_sizes: Dict[str, int] = {}
        for repo in original_repos:
            for edge in repo.get("languages", {}).get("edges", []):
                lang = edge["node"]["name"]
                size = edge["size"]
                lang_sizes[lang] = lang_sizes.get(lang, 0) + size

        total_size = sum(lang_sizes.values()) or 1
        top_languages = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:10]
        language_percentages = {
            lang: round((size / total_size) * 100, 1)
            for lang, size in top_languages
        }

        # Contribution data
        contrib = data.get("contributionsCollection", {})
        calendar = contrib.get("contributionCalendar", {})
        all_days = [
            day
            for week in calendar.get("weeks", [])
            for day in week.get("contributionDays", [])
        ]
        active_days = sum(1 for d in all_days if d["contributionCount"] > 0)

        # Streak calculation
        current_streak = self._calc_streak(all_days)

        # Stars and forks
        total_stars = sum(r["stargazerCount"] for r in original_repos)
        total_forks_received = sum(r["forkCount"] for r in original_repos)

        # Commit counts
        total_commits_approx = sum(
            (r.get("defaultBranchRef") or {})
            .get("target", {})
            .get("history", {})
            .get("totalCount", 0)
            for r in original_repos
        )

        # Account age
        created_at = data.get("createdAt", "")
        account_age_days = 0
        if created_at:
            try:
                created_date = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                account_age_days = (datetime.datetime.now(datetime.timezone.utc) - created_date).days
            except Exception:
                pass

        primary_languages = list(dict.fromkeys(
            r["primaryLanguage"]["name"]
            for r in original_repos
            if r.get("primaryLanguage")
        ))[:5]

        return {
            # Identity
            "username": username,
            "name": data.get("name") or username,
            "bio": data.get("bio") or "",
            "location": data.get("location") or "Not specified",

            # Repository metrics
            "total_repos": data["repositories"]["totalCount"],
            "original_repos": len(original_repos),
            "active_repos_last_year": len(active_repos),
            "forked_repos": len(repos) - len(original_repos),

            # Engagement metrics
            "total_stars": total_stars,
            "total_forks_received": total_forks_received,
            "followers": data["followers"]["totalCount"],
            "following": data["following"]["totalCount"],

            # Activity metrics
            "merged_prs": data["pullRequests"]["totalCount"],
            "open_issues": data["issues"]["totalCount"],
            "total_contributions_year": calendar.get("totalContributions", 0),
            "total_commits_approx": total_commits_approx,
            "active_days_year": active_days,
            "current_streak_days": current_streak,

            # Language metrics
            "languages": list(language_percentages.keys()),
            "language_percentages": language_percentages,
            "primary_languages": primary_languages,
            "language_diversity": len(lang_sizes),

            # Account health
            "account_age_days": account_age_days,
            "commit_contributions": contrib.get("totalCommitContributions", 0),
            "pr_contributions": contrib.get("totalPullRequestContributions", 0),
            "issue_contributions": contrib.get("totalIssueContributions", 0),
        }

    def _is_recent(self, date_str: str, days: int) -> bool:
        try:
            date = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
            return date > cutoff
        except Exception:
            return False

    def _calc_streak(self, days: List[Dict]) -> int:
        streak = 0
        for day in reversed(days):
            if day["contributionCount"] > 0:
                streak += 1
            else:
                break
        return streak