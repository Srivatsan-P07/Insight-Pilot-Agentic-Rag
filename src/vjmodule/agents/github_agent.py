"""GitHub Integration agent — PR, commit, and repository analysis.

Set GITHUB_TOKEN in .env for authenticated access (5 000 req/hr vs 60/hr).
"""
from __future__ import annotations

import json
from typing import Optional, Generator

from config import Config
from connectors.github import GitHubConnector


# def stream_github_analysis(
#     question: str,
#     repo: Optional[str] = None,
# ) -> Generator[str, None, None]:
#     """Yield streaming GitHub analysis for *repo* (format: ``owner/name``)."""
#     connector = GitHubConnector()
#     username  = connector.whoami()

#     if not connector.is_authenticated():
#         yield (
#             "⚠️ **No GitHub token configured.**\n\n"
#             "Add `GITHUB_TOKEN=ghp_yourtoken` to your `.env` file.\n"
#             "Generate a token with `repo` scope at: https://github.com/settings/tokens\n\n"
#             "_Continuing with unauthenticated access (rate-limited to 60 req/hr)..._\n\n"
#         )

#     context_parts: list[str] = [
#         f"**GitHub User:** `{username or 'anonymous'}`"
#     ]

#     if repo:
#         yield f"_Fetching data from `{repo}`..._\n\n"
#         open_prs = connector.get_recent_open_prs()
#         pr_reviews = []

#         for pr in open_prs[:2]:

#             files = connector.get_pr_files(
#                 pr["repo"],
#                 pr["number"]
#             )

#             pr_reviews.append({
#                 "repo": pr["repo"],
#                 "number": pr["number"],
#                 "title": pr["title"],
#                 "files": files
#             })
        
#         context_parts.append(
#                 f"""
#             **PR DIFFS**
#             ```json
#             {json.dumps(pr_reviews, indent=2)}
#             ```
#         """
#         )

#         open_prs = connector.get_recent_open_prs(limit=2)

#         pr_details = []

#         for pr in open_prs:

#             files = connector.get_pr_files(
#                 pr["repo"],
#                 pr["number"]
#             )

#             pr_details.append({
#                 **pr,
#                 "files": files
#             })
#         context_parts.append(
#             f"""
#         **OPEN PR DETAILS**
#         ```json
#         {json.dumps(pr_details, indent=2)}
#         ```
#         """
#         )

#         latest_pr = open_prs[0]

#         review_context = connector.get_pr_review_context(
#             latest_pr["repo"],
#             latest_pr["number"]
#         )
#         context_parts.append(
#             f"""
#             PR REVIEW DATA

#             ```json
#             {json.dumps(review_context, indent=2)}
#             ```
#             """
#         )
#         commits = connector.get_recent_commits(repo, limit=15)
#         context_parts += [
#             f"\n**Repository:** `{repo}`",
#             f"\n**Open PRs ({len(open_prs)}):**\n```json\n{json.dumps(open_prs, indent=2, default=str)}\n```",
#             f"\n**Recent Commits ({len(commits)}):**\n```json\n{json.dumps(commits, indent=2, default=str)}\n```",
#         ]
#     else:
#         # yield "_Loading your repositories..._\n\n"
#         # repos = connector.list_repos(limit=20)
#         # context_parts.append(
#         #     f"\n**Your repositories:**\n```json\n{json.dumps(repos, indent=2, default=str)}\n```"
#         # )
#         yield "_Loading your repositories..._\n\n"

#         repos = connector.list_repos(limit=10)

#         context_parts.append(
#             f"\n**Your repositories:**\n```json\n{json.dumps(repos, indent=2)}\n```"
#         )
        
#         recent_prs = []

#         for repo_info in repos[:5]:
#             repo_name = repo_info["full_name"]

#             prs = connector.get_recent_open_prs(limit=10)

#             for pr in prs:
#                 if "error" not in pr:
#                     pr["repo"] = repo_name
#                     recent_prs.append(pr)

#         context_parts.append(
#             f"\n**Recent Open Pull Requests:**\n```json\n"
#             f"{json.dumps(recent_prs[:10], indent=2)}\n```"
#         )

#     context = "\n".join(context_parts)

#     prompt = f"""You are a senior software engineer and code-review expert.

# === GITHUB CONTEXT ===
# {context}
# ======================

# User question: {question}

# You are a Principal Software Engineer.

# Analyze the PR diff and provide:

# ## Executive Summary

# Brief explanation of:
# - What existed before
# - What changed
# - Why the change was made

# ## Functional Impact

# Explain how system behaviour changes.

# ## Performance Impact

# Identify:
# - Faster execution?
# - Less memory?
# - Less API calls?
# - Less DB queries?

# If no improvement exists say:
# "No measurable performance improvement."

# ## Code Quality Review

# Highlight:

# ✓ Good practices

# ⚠ Possible improvements

# ❌ Bugs or risks

# ## Security Review

# Review:
# - Secrets
# - Tokens
# - Input validation
# - SQL injection
# - Authentication

# ## Suggested Code Improvements

# Provide improved code snippets.

# ## PR Description Improvement

# Generate an ideal PR description.

# ## Reviewer Comments

# Generate reviewer comments that would typically be added on GitHub.
# """
# # Respond with:

# # If open pull requests are available and the user asks about PRs:

# # 1. Identify the 2 most recently updated PRs.
# # 2. Summarize each PR.
# # 3. Highlight risk areas.
# # 4. Mention files changed if available.
# # 5. Mention additions/deletions if available.

# # Format:

# # ## 💬 Direct Answer

# # ### PR #<number> - <title>
# # - Repository:
# # - Author:
# # - Updated:
# # - Summary:
# # - Risk:

# # ### PR #<number> - <title>
# # - Repository:
# # - Author:
# # - Updated:
# # - Summary:
# # - Risk:

# # ## 🔍 Code Quality Insights

# # ## ✅ Action Items

# # ## 🏆 Best Practices

# # ## ➡️ Next Steps

# # Use markdown. Include code snippets where relevant.
# # """

#     try:
#         for chunk in Config.llm.stream(prompt):
#             if chunk.content:
#                 yield chunk.content
#     except Exception as exc:
#         yield f"\n\n❌ **Error:** {exc}"



def stream_github_analysis(
    question: str,
    repo: Optional[str] = None,
    ) -> Generator[str, None, None]:
    """
    Yield streaming GitHub analysis.

    If repo is supplied:
        - Analyze PRs for that repo
    Else:
        - Analyze latest open PRs across repositories
    """

    connector = GitHubConnector()
    username = connector.whoami()

    if not connector.is_authenticated():
        yield (
            "⚠️ **No GitHub token configured.**\n\n"
            "Add `GITHUB_TOKEN=ghp_yourtoken` to your `.env` file.\n"
            "Generate a token with `repo` scope.\n\n"
            "_Continuing with unauthenticated access (rate-limited to 60 req/hr)..._\n\n"
        )

    context_parts = [
        f"**GitHub User:** `{username or 'anonymous'}`"
    ]

    try:

        # ==========================================================
        # SPECIFIC REPOSITORY
        # ==========================================================
        if repo:

            yield f"_Fetching data from `{repo}`..._\n\n"

            commits = connector.get_recent_commits(
                repo,
                limit=15
            )

            # Use repo-specific PRs
            prs = connector.get_recent_prs(
                repo_full_name=repo,
                state="open",
                limit=2
            )

            pr_reviews = []

            for pr in prs:

                if "error" in pr:
                    continue

                files = connector.get_pr_files(
                    repo,
                    pr["number"]
                )

                pr_reviews.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr["author"],
                    "updated_at": pr["updated_at"],
                    "files_changed": pr.get("files_changed"),
                    "additions": pr.get("additions"),
                    "deletions": pr.get("deletions"),
                    "files": files
                })

            context_parts.extend([
                f"\n**Repository:** `{repo}`",
                f"\n**Open PR Reviews:**\n```json\n{json.dumps(pr_reviews, indent=2)}\n```",
                f"\n**Recent Commits:**\n```json\n{json.dumps(commits, indent=2)}\n```"
            ])

        # ==========================================================
        # ALL REPOSITORIES
        # ==========================================================
        else:

            yield "_Loading your repositories..._\n\n"

            repos = connector.list_repos(limit=20)

            open_prs = connector.get_recent_open_prs(
                limit=2
            )

            pr_reviews = []

            for pr in open_prs:

                if "error" in pr:
                    continue

                files = connector.get_pr_files(
                    pr["repo"],
                    pr["number"]
                )

                pr_reviews.append({
                    "repo": pr["repo"],
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr["author"],
                    "updated_at": pr["updated_at"],
                    "files_changed": pr.get("files_changed"),
                    "additions": pr.get("additions"),
                    "deletions": pr.get("deletions"),
                    "files": files
                })

            context_parts.extend([
                f"\n**Repositories:**\n```json\n{json.dumps(repos, indent=2)}\n```",
                f"\n**Latest Open PR Reviews:**\n```json\n{json.dumps(pr_reviews, indent=2)}\n```"
            ])

        context = "\n".join(context_parts)

        prompt = f'''

    You are a Principal Software Engineer performing a senior-level GitHub Pull Request review.

    {context}

    {question}

    IMPORTANT:

    PR file patches/diffs are already included in the context.
    DO NOT ask for diffs again.
    Analyze the supplied patch data.
    Infer:
    what existed before
    what changed
    why the change was made
    If a patch is available, provide code review comments.
    Only say "Insufficient information" if no patch exists.

    For EACH PR provide:

    Executive Summary
    What existed before
    What changed
    Why the change was made
    Functional Impact

    Explain behavioural changes.

    Performance Impact

    Discuss:

    execution speed
    memory usage
    network calls
    database calls

    If no measurable impact exists,
    explicitly state so.

    Code Quality Review
    Good Practices
    Improvements
    Bugs / Risks
    Security Review

    Review:

    secrets
    tokens
    authentication
    authorization
    input validation
    injection risks
    Suggested Code Improvements

    Provide improved code snippets when useful.

    PR Description Improvement

    Generate a professional PR description.

    Reviewer Comments

    Generate realistic GitHub review comments.

    Merge Recommendation

    Choose one:

    APPROVE
    APPROVE WITH COMMENTS
    REQUEST CHANGES

    Explain why.
    '''

        for chunk in Config.llm.stream(prompt):
            if chunk.content:
                yield chunk.content

    except Exception as exc:
        yield f"\n\n❌ **Error:** {str(exc)}"