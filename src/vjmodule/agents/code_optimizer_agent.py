"""Code Cost Optimizer agent — GCP cost & performance analysis of source code.

Modes (auto-detected from the user's question):
  cost  — query contains cost/billing/savings keywords
          → shows current cost estimate vs post-fix estimate with per-issue savings
  perf  — no cost keywords
          → pure performance / code-quality improvements for faster execution

Code sources (checked in priority order):
  1. GitHub path detected inside the message  (owner/repo  or  owner/repo/src/folder)
  2. github_repo from session state (the repo set in the GitHub agent tab)
  3. Code pasted directly in the message (fenced or raw)
"""
from __future__ import annotations

import re
from typing import Generator, Optional

from config import GCPConfig

# ── Patterns ──────────────────────────────────────────────────────────────────

_COST_KEYWORDS = re.compile(
    r"\b(cost|billing|expensive|sav(e|ing|ings)|cheap|money|\$|budget|spend"
    r"|optimis(e|ing)|optimi[zs]e\s+cost|analyse\s+(cost|billing))\b",
    re.IGNORECASE,
)

_FENCE_RE = re.compile(r"```(?:\w+)?\n?(.*?)```", re.DOTALL)

# GitHub reserved path segments — never valid as repo/owner names
_GH_RESERVED = {"blob", "tree", "commit", "releases", "issues", "pulls", "actions", "wiki"}

# Full blob URL:  owner/repo/blob/branch/path/to/file.py
_GITHUB_BLOB_RE = re.compile(
    r"(?:https?://)?(?:github\.com/)?"
    r"(?P<owner>[a-zA-Z0-9][a-zA-Z0-9\-]{0,38})"
    r"/(?P<repo>[a-zA-Z0-9_\-\.]{2,100})"
    r"/blob/"
    r"(?P<branch>[^/\s]+)"
    r"/(?P<path>[^\s\"'`\)\]]+)",
)

# Blob URL WITHOUT owner:  repo/blob/branch/path  (owner missing)
_GITHUB_BLOB_NO_OWNER_RE = re.compile(
    r"(?<![/\w])"
    r"(?P<repo>[a-zA-Z0-9_\-\.]{2,100})"
    r"/blob/"
    r"(?P<branch>[^/\s]+)"
    r"/(?P<path>[^\s\"'`\)\]]+)",
)

# Plain:  owner/repo  or  owner/repo/path/to/folder
_GITHUB_PATH_RE = re.compile(
    r"(?:https?://)?(?:github\.com/)?"
    r"([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?)"
    r"/"
    r"([a-zA-Z0-9_\-\.]{1,100})"
    r"(?:/([^\s\"'`\)\]]+))?",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_github_path(message: str) -> Optional[tuple[str, str, str]]:
    """Return (repo_full_name, path, branch) or None.

    Handles three input styles:
      - owner/repo/blob/branch/file.py   (full blob URL)
      - repo/blob/branch/file.py         (blob URL missing owner — auto-resolves via whoami)
      - owner/repo/path/to/folder        (plain path)
    """
    # 1. Full blob URL with owner
    for m in _GITHUB_BLOB_RE.finditer(message):
        owner  = m.group("owner")
        repo   = m.group("repo")
        branch = m.group("branch")
        path   = m.group("path")
        if repo.lower() in _GH_RESERVED:
            continue
        return f"{owner}/{repo}", path, branch

    # 2. Blob URL without owner — try to resolve owner from GitHub identity
    for m in _GITHUB_BLOB_NO_OWNER_RE.finditer(message):
        repo   = m.group("repo")
        branch = m.group("branch")
        path   = m.group("path")
        if repo.lower() in _GH_RESERVED:
            continue
        try:
            from vjmodule.connectors.github import GitHubConnector
            owner = GitHubConnector().whoami() or ""
        except Exception:
            owner = ""
        if owner:
            return f"{owner}/{repo}", path, branch
        return f"__MISSING_OWNER__/{repo}", path, branch

    # 3. Plain owner/repo[/path]
    for m in _GITHUB_PATH_RE.finditer(message):
        owner, repo, path = m.group(1), m.group(2), m.group(3) or ""
        if len(owner) < 2 or len(repo) < 2:
            continue
        if repo.lower() in _GH_RESERVED:
            continue
        # Skip GCP region patterns like "us-central1"
        if re.fullmatch(r"[a-z]+-[a-z0-9]+", owner):
            continue
        if re.fullmatch(r"[a-z]{1,4}", owner):
            continue
        # Strip any leftover blob/tree prefix from path
        path = re.sub(r"^(?:blob|tree)/[^/]+/", "", path)
        return f"{owner}/{repo}", path, ""

    return None


def _split_code_and_question(message: str) -> tuple[str, str]:
    """Return (code, plain_question) extracted from a freeform message."""
    fences = _FENCE_RE.findall(message)
    if fences:
        code     = "\n\n".join(fences).strip()
        question = _FENCE_RE.sub("", message).strip()
        return code, question

    lines      = message.splitlines()
    code_lines = sum(
        1 for ln in lines
        if ln.strip().startswith(("#", "def ", "class ", "import ", "from ", "//", "/*", "{", "}", "  "))
    )
    if lines and code_lines / len(lines) > 0.30:
        return message.strip(), ""
    return "", message.strip()


def _fetch_github_code(repo_full_name: str, path: str, branch: str = "") -> tuple[str, str]:
    """Return (formatted_code_block, status_message)."""
    if repo_full_name.startswith("__MISSING_OWNER__/"):
        repo = repo_full_name.split("/", 1)[1]
        return "", (
            f"⚠️ Could not determine the GitHub owner for `{repo}`.\n\n"
            f"Please include the owner in your message, e.g.:\n"
            f"`your-username/{repo}/blob/{branch}/{path}`"
        )
    try:
        from vjmodule.connectors.github import GitHubConnector
        connector = GitHubConnector()
        files = connector.get_folder_contents(
            repo_full_name, path=path, max_files=20,
            ref=branch if branch else None,
        )

        if not files:
            return "", f"No code files found at `{repo_full_name}/{path or '(root)'}`"
        if "error" in files[0]:
            return "", f"GitHub error: {files[0]['error']}"

        blocks = []
        for f in files:
            ext = f["path"].rsplit(".", 1)[-1] if "." in f["path"] else ""
            blocks.append(f"### {f['path']}\n```{ext}\n{f['content']}\n```")

        label = f"{repo_full_name}/{path}" if path else repo_full_name
        return "\n\n".join(blocks), f"Fetched {len(files)} files from `{label}`"
    except Exception as exc:
        return "", f"Could not fetch from GitHub: {exc}"


def _fetch_billing_context(project_id: str) -> str:
    """Return a short cost summary string, or empty string on any failure."""
    try:
        from vjmodule.connectors.gcp_billing import get_cost_summary
        summary = get_cost_summary(project_id, days=30)
        cost_df = summary["cost_data"]
        billing = summary["billing_info"]

        if "status" in cost_df.columns:
            return (
                f"Billing account: {billing.get('billing_account', 'N/A')} | "
                "BigQuery billing export not configured — exact figures unavailable."
            )
        if "error" in cost_df.columns:
            return ""

        total   = cost_df["total_cost"].sum()
        top_svc = cost_df.groupby("service")["total_cost"].sum().nlargest(5)
        return (
            f"**30-day total spend (project `{project_id}`):** ${total:,.2f}\n"
            f"**Top 5 services:**\n{top_svc.to_string()}"
        )
    except Exception:
        return ""


# ── Agent ─────────────────────────────────────────────────────────────────────

def stream_code_optimization(
    message: str,
    project_id: str = "",
    github_repo: str = "",
) -> Generator[str, None, None]:
    """Yield streaming code analysis.

    Auto-detects:
    - Cost mode  (message contains cost/billing keywords) → diff before/after cost
    - Perf mode  (no cost keywords)                       → speed & quality review

    Code is pulled from GitHub if a path is found in the message or github_repo
    is set; otherwise falls back to pasted code.
    """
    is_cost_query = bool(_COST_KEYWORDS.search(message))

    # ── Resolve code source ───────────────────────────────────────────────────
    code_context = ""
    source_label = ""

    # Priority 1: GitHub path embedded in the message
    github_in_msg = _detect_github_path(message)
    if github_in_msg:
        repo_name, folder_path, branch = github_in_msg
        display = f"{repo_name}/{folder_path}" if folder_path else repo_name
        branch_label = f" @ `{branch}`" if branch else ""
        yield f"_Fetching code from GitHub: `{display}`{branch_label}…_\n\n"
        code_context, status = _fetch_github_code(repo_name, folder_path, branch)
        source_label = status
        if not code_context:
            yield f"{status}\n\n"
            return

    # Priority 2: github_repo from session state (repo set in GitHub agent tab)
    if not code_context and github_repo:
        yield f"_Fetching code from `{github_repo}`…_\n\n"
        code_context, status = _fetch_github_code(github_repo, "", "")
        source_label = status
        if not code_context:
            yield f"⚠️ {status}\n\n"

    # Priority 3: pasted code in the message
    if not code_context:
        pasted_code, _ = _split_code_and_question(message)
        if pasted_code:
            code_context = f"```\n{pasted_code}\n```"
            source_label = "pasted code"

    if not code_context:
        yield (
            "Please provide code to analyse. You can:\n"
            "- **Paste code** directly (or inside ` ```fences``` `)\n"
            "- **GitHub path** in your message: `owner/repo` or `owner/repo/src/folder`\n"
            "- **Set a repo** in the GitHub field above, then ask your question"
        )
        return

    # ── Billing context (only in cost mode when a project is selected) ────────
    billing_context = ""
    if is_cost_query and project_id:
        yield f"_Fetching billing data for `{project_id}`…_\n\n"
        billing_context = _fetch_billing_context(project_id)

    # ── Build prompt ──────────────────────────────────────────────────────────
    project_note = ""
    if project_id:
        if billing_context:
            project_note = f"\n=== CURRENT GCP BILLING (project: {project_id}) ===\n{billing_context}\n===================================================\n"
        else:
            project_note = f"\n_GCP project `{project_id}` is selected. No billing export data available — use estimates._\n"

    if is_cost_query:
        prompt = f"""You are a GCP FinOps engineer. Be concise — no filler text.
{project_note}
=== CODE ({source_label}) ===
{code_context}
==============================

Question: {message}

For every issue found, use EXACTLY this block — no extra prose:

---
**[HIGH/MEDIUM/LOW] One-line issue title** — `filename:line`

_Current code:_
```language
// exact problematic lines from the file
```
_Optimised:_
```language
// corrected replacement
```
💰 Saving: **$X/day · $X/month · $X/year** (state "estimate" if no billing data)

---

After all issues, one compact table:
| Total savings | Per day | Per month | Per year |
|---|---|---|---|
| Combined | $X | $X | $X |

Then one line each:
- ⚡ **Biggest quick win:** ...
- 🏗️ **Long-term:** ...

No summaries. No "what's already good" section. Output issues only."""

    else:
        prompt = f"""You are a senior engineer. Be concise — no filler text.

=== CODE ({source_label}) ===
{code_context}
==============================

Question: {message}

For every performance issue found, use EXACTLY this block:

---
**[CRITICAL/HIGH/MEDIUM] One-line issue title** — `filename:line`

_Current code:_
```language
// exact slow lines from the file
```
_Optimised:_
```language
// faster replacement
```
⚡ Gain: **Xms faster / X× throughput / X% less memory** (be specific)

---

After all issues, two lines only:
- 🚀 **Biggest quick win:** ...
- 🏗️ **Architectural change:** ...

No summaries. No "what's already good" section. Output issues only."""

    try:
        for chunk in GCPConfig.get_llm().stream(prompt):
            if chunk.content:
                yield chunk.content
    except Exception as exc:
        yield f"\n\n❌ **Error during analysis:** {exc}"
