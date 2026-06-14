"""GitHub connector — PyGithub wrapper for PR, commit and repo analysis.

Authentication: set GITHUB_TOKEN in your .env file.
Without a token, the GitHub API rate-limit is very restrictive (60 req/hr).
"""
from __future__ import annotations

import os
from typing import Optional


class GitHubConnector:
    """Authenticated GitHub client backed by PyGithub."""

    def __init__(self, token: Optional[str] = None):
        from github import Github

        _token = token or os.getenv("GITHUB_TOKEN")
        self._gh = Github(_token) if _token else Github()
        self._authenticated = bool(_token)

    # ── Identity ─────────────────────────────────────────────────────────────

    def whoami(self) -> Optional[str]:
        try:
            return self._gh.get_user().login
        except Exception:
            return None

    def is_authenticated(self) -> bool:
        return self._authenticated

    # ── Repositories ─────────────────────────────────────────────────────────

    def list_repos(self, org: Optional[str] = None, limit: int = 30) -> list[dict]:
        try:
            source = (
                self._gh.get_organization(org).get_repos()
                if org
                else self._gh.get_user().get_repos(sort="updated")
            )
            return [
                {
                    "full_name":   r.full_name,
                    "name":        r.name,
                    "description": r.description or "",
                    "language":    r.language or "",
                    "stars":       r.stargazers_count,
                    "private":     r.private,
                    "updated_at":  r.updated_at.isoformat() if r.updated_at else "",
                }
                for r in list(source)[:limit]
            ]
        except Exception as exc:
            return [{"error": str(exc)}]

    # ── Pull Requests ─────────────────────────────────────────────────────────

    # def get_recent_prs(
    #     self,
    #     repo_full_name: str,
    #     state: str = "open",
    #     limit: int = 10,
    # ) -> list[dict]:
    #     try:
    #         repo = self._gh.get_repo(repo_full_name)
    #         return [
    #             {
    #                 "number":        pr.number,
    #                 "title":         pr.title,
    #                 "author":        pr.user.login,
    #                 "state":         pr.state,
    #                 "created_at":    pr.created_at.isoformat(),
    #                 "updated_at":    pr.updated_at.isoformat(),
    #                 "body":          (pr.body or "")[:400],
    #                 "url":           pr.html_url,
    #                 "files_changed": pr.changed_files,
    #                 "additions":     pr.additions,
    #                 "deletions":     pr.deletions,
    #                 "labels":        [lb.name for lb in pr.labels],
    #             }
    #             for pr in list(
    #                 repo.get_pulls(state=state, sort="updated", direction="desc")
    #             )[:limit]
    #         ]
    #     except Exception as exc:
    #         return [{"error": str(exc)}]

    def get_recent_open_prs(
    self,
    limit: int = 20
    ) -> list[dict]:

        repos = self._gh.get_user().get_repos(sort="updated")

        prs = []

        for repo in repos:
            try:
                for pr in repo.get_pulls(
                    state="open",
                    sort="updated",
                    direction="desc"
                ):
                    prs.append({
                        "repo": repo.full_name,
                        "number": pr.number,
                        "title": pr.title,
                        "updated_at": pr.updated_at.isoformat(),
                        "author": pr.user.login,
                        "url": pr.html_url,
                    })
            except Exception:
                pass

        prs.sort(
            key=lambda x: x["updated_at"],
            reverse=True
        )

        return prs[:limit]

    # ── Commits ───────────────────────────────────────────────────────────────

    def get_recent_commits(
        self,
        repo_full_name: str,
        branch: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        try:
            repo = self._gh.get_repo(repo_full_name)
            kwargs = {"sha": branch} if branch else {}
            return [
                {
                    "sha":       c.sha[:8],
                    "message":   c.commit.message.split("\n")[0],
                    "author":    c.commit.author.name,
                    "date":      c.commit.author.date.isoformat(),
                    "url":       c.html_url,
                    "additions": c.stats.additions,
                    "deletions": c.stats.deletions,
                }
                for c in list(repo.get_commits(**kwargs))[:limit]
            ]
        except Exception as exc:
            return [{"error": str(exc)}]
        
    def get_pr_details(
        self,
        repo_full_name: str,
        pr_number: int,
    ) -> dict:
        try:
            repo = self._gh.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "files": self.get_pr_files(
                    repo_full_name,
                    pr_number
                )
            }

        except Exception as exc:
            return {"error": str(exc)}
        
    def get_pr_review_context(
        self,
        repo_full_name: str,
        pr_number: int
    ) -> dict:

        try:
            repo = self._gh.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            files = []

            for f in pr.get_files():

                files.append({
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "patch": f.patch
                })

            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "files": files
            }

        except Exception as exc:
            return {"error": str(exc)}
    # ── Folder / file contents ────────────────────────────────────────────────

    def get_folder_contents(
        self,
        repo_full_name: str,
        path: str = "",
        max_files: int = 20,
        extensions: Optional[list[str]] = None,
        ref: Optional[str] = None,
    ) -> list[dict]:
        """Recursively fetch code file contents from *path* in *repo_full_name*.

        *ref* can be a branch name, tag, or commit SHA (e.g. ``main``,
        ``VIJAYVIVU-patch-1``).  Defaults to the repo's default branch.
        Returns up to *max_files* files filtered by extension.
        Each file is capped at 8 000 chars to stay within LLM token limits.
        """
        _CODE_EXTS = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb",
            ".php", ".cs", ".cpp", ".c", ".h", ".sql", ".sh",
            ".yaml", ".yml", ".tf", ".toml",
        }
        allowed = set(extensions) if extensions else _CODE_EXTS
        get_kw = {"ref": ref} if ref else {}

        try:
            repo  = self._gh.get_repo(repo_full_name)
            files: list[dict] = []

            def _recurse(dir_path: str) -> None:
                if len(files) >= max_files:
                    return
                try:
                    contents = repo.get_contents(dir_path, **get_kw)
                except Exception:
                    return
                if not isinstance(contents, list):
                    contents = [contents]
                for item in contents:
                    if len(files) >= max_files:
                        break
                    if item.type == "dir":
                        _recurse(item.path)
                    elif item.type == "file":
                        ext = os.path.splitext(item.name)[1].lower()
                        if ext in allowed and item.size <= 100_000:
                            try:
                                content = item.decoded_content.decode("utf-8", errors="replace")
                                files.append({
                                    "path":    item.path,
                                    "size":    item.size,
                                    "content": content[:8_000],
                                })
                            except Exception:
                                pass

            _recurse(path)
            return files
        except Exception as exc:
            return [{"error": str(exc)}]

    # ── PR diff / files ───────────────────────────────────────────────────────

    def get_pr_files(self, repo_full_name: str, pr_number: int) -> list[dict]:
        try:
            repo = self._gh.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            return [
                {
                    "filename":  f.filename,
                    "status":    f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "patch":     (f.patch or "")[:3000],
                }
                for f in pr.get_files()
            ]
        except Exception as exc:
            return [{"error": str(exc)}]
