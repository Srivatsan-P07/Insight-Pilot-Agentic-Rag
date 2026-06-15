"""Insight Pilot — AI-powered GCP intelligence & data platform.

Home screen   : search bar + agent tiles grid
Agent screen  : Copilot-style streaming chat with back navigation
"""
from __future__ import annotations

import streamlit as st

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insight Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — Copilot-style dark UI ───────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Backgrounds ─────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] > .main { background: #0d0d1a; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stSidebar"]          { background: #111120; }
section[data-testid="stMain"] > div { padding-top: 1.5rem; }

/* ── Hero text ───────────────────────────────────────────────────── */
.ip-hero-title {
    font-size: 2.5rem; font-weight: 800;
    background: linear-gradient(135deg, #4a8fff 0%, #9b5de5 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0; line-height: 1.2;
}
.ip-hero-sub {
    color: #7070a0; font-size: 1.05rem; margin-bottom: 2rem;
}

/* ── Section label ───────────────────────────────────────────────── */
.ip-section {
    color: #5a5a8a; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 1.8px; text-transform: uppercase;
    margin: 1.6rem 0 0.6rem 0;
}

/* ── Agent tile buttons ──────────────────────────────────────────── */
div[data-testid="stVerticalBlock"] div.stButton > button {
    background: #13132a;
    border: 1px solid #252545;
    border-radius: 14px;
    color: #d0d0f0;
    padding: 18px 20px;
    text-align: left;
    min-height: 118px;
    height: auto;
    font-size: 0.88rem;
    line-height: 1.6;
    white-space: pre-wrap;
    transition: border-color 0.18s, box-shadow 0.18s, transform 0.18s;
    width: 100%;
}
div[data-testid="stVerticalBlock"] div.stButton > button:hover {
    border-color: #4a8fff;
    box-shadow: 0 0 16px rgba(74,143,255,0.25);
    transform: translateY(-2px);
    color: #ffffff;
}

/* ── Agent header bar ────────────────────────────────────────────── */
.ip-agent-bar {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0 14px 0;
    border-bottom: 1px solid #252545;
    margin-bottom: 18px;
}
.ip-agent-bar .ip-dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #22cc77; flex-shrink: 0;
}
.ip-agent-bar .ip-title  { font-size: 1.2rem; font-weight: 700; color: #e0e0ff; }
.ip-agent-bar .ip-sub    { font-size: 0.82rem; color: #6060a0; margin-top: 1px; }

/* ── Chat messages ───────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #13132a;
    border: 1px solid #1e1e3e;
    border-radius: 12px;
    margin-bottom: 10px;
}

/* ── Chat input ──────────────────────────────────────────────────── */
[data-testid="stChatInputTextArea"] {
    background: #13132a !important;
    border: 1px solid #2d2d55 !important;
    border-radius: 12px !important;
    color: #e0e0ff !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInputTextArea"]:focus {
    border-color: #4a8fff !important;
    box-shadow: 0 0 0 2px rgba(74,143,255,0.18) !important;
}

/* ── Text / select inputs ────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div {
    background: #13132a !important;
    color: #e0e0ff !important;
    border: 1px solid #2d2d55 !important;
    border-radius: 10px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #4a8fff !important;
}

/* ── Metrics ─────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #13132a; border: 1px solid #252545;
    border-radius: 10px; padding: 12px;
}

/* ── Form search ─────────────────────────────────────────────────── */
.ip-search-wrap [data-testid="stTextInput"] input {
    border-radius: 24px !important;
    padding: 10px 20px !important;
    font-size: 1rem !important;
}

/* ── Generating indicator ────────────────────────────────────────── */
.ip-generating {
    color: #5a5a9a; font-size: 0.85rem; font-style: italic;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Agent registry ────────────────────────────────────────────────────────────
AGENTS: list[dict] = [
    {
        "id":               "gcp_cost",
        "title":            "GCP Cost Analyser",
        "subtitle":         "All Services",
        "icon":             "💰",
        "desc":             "Full-stack cost visibility across all GCP services and projects",
        "requires_project": True,
        "requires_github":  False,
        "placeholder":      "Ask about cost trends, top spenders, budget alerts...",
        "welcome":          (
            "👋 I'm your **GCP Cost Analyser**.\n\n"
            "Select a project from the dropdown above, then ask me anything about your cloud spend — "
            "e.g. *\"What are my top 5 cost drivers this month?\"* or "
            "*\"Show me any cost spikes in the last 30 days.\"*"
        ),
    },
    {
        "id":               "gcp_recommender",
        "title":            "GCP Recommender",
        "subtitle":         "Automated Optimisation",
        "icon":             "🔧",
        "desc":             "Live AI-powered optimisation suggestions with savings estimates",
        "requires_project": True,
        "requires_github":  False,
        "placeholder":      "Show all active recommendations, explain idle VM savings...",
        "welcome":          (
            "👋 I'm your **GCP Optimisation Advisor**.\n\n"
            "Select a project and I'll pull live recommendations from the GCP Recommender API — "
            "idle VMs, rightsizing opportunities, commitment discounts, IAM policy cleanups, and more."
        ),
    },
    {
        "id":               "github",
        "title":            "GitHub Integration",
        "subtitle":         "PR & Commit Analysis",
        "icon":             "🐙",
        "desc":             "Analyse pull requests, commits, and repositories with AI",
        "requires_project": False,
        "requires_github":  True,
        "placeholder":      "Summarise open PRs, review commit quality, list repos...",
        "welcome":          (
            "👋 I'm your **GitHub Assistant**.\n\n"
            "Enter a repository (`owner/repo`) in the field above, then ask me anything — "
            "*\"Summarise the 5 most recent open PRs\"* or *\"What changed in the last 10 commits?\"*\n\n"
            "Add `GITHUB_TOKEN=ghp_xxx` to your `.env` for authenticated access."
        ),
    },
    {
        "id":               "code_optimizer",
        "title":            "Code Cost Optimizer",
        "subtitle":         "GitHub · Paste Code · Get Savings",
        "icon":             "💡",
        "desc":             "Detect GCP cost inefficiencies or performance issues in code — from GitHub or pasted",
        "requires_project": True,
        "requires_github":  True,
        "placeholder":      "Paste code, give a GitHub path (owner/repo/folder), or just ask a question...",
        "welcome":          (
            "👋 I'm your **Code Cost Optimizer**.\n\n"
            "I work in two modes — auto-detected from your question:\n"
            "- **💸 Cost mode** *(mention cost/billing/savings)* — fetches your live GCP billing, "
            "shows current vs optimised cost per issue with $ savings estimates\n"
            "- **⚡ Perf mode** *(no cost keywords)* — pure performance & code quality improvements\n\n"
            "**How to give me code:**\n"
            "1. **Full GitHub URL:** `https://github.com/owner/repo/blob/branch/file.py`\n"
            "2. **Short path:** `owner/repo` or `owner/repo/src/folder`\n"
            "3. **Set a repo** in the GitHub field above, then ask your question\n"
            "4. **Paste code** directly (fenced or raw)\n\n"
            "*Example: `optimise VIJAYVIVU/data_api_hits/blob/main/temp.py` or "
            "`analyse myorg/myrepo/src/bigquery for cost`*"
        ),
    },
    {
        "id":               "docs",
        "title":            "Documentation Search",
        "subtitle":         "Confluence Knowledge Base",
        "icon":             "📚",
        "desc":             "Semantic AI search across your Confluence documentation",
        "requires_project": False,
        "requires_github":  False,
        "placeholder":      "Search processes, definitions, architecture docs...",
        "welcome":          (
            "👋 I'm your **Docs Assistant**.\n\n"
            "I perform semantic search across your Confluence knowledge base using vector embeddings. "
            "Ask me about processes, definitions, architecture decisions, or any internal documentation."
        ),
    },
    {
        "id":               "sql",
        "title":            "SQL Analytics",
        "subtitle":         "BigQuery Intelligence",
        "icon":             "🗄️",
        "desc":             "Natural language to SQL with automatic data analysis",
        "requires_project": False,
        "requires_github":  False,
        "placeholder":      "Ask questions about your data in plain English...",
        "welcome":          (
            "👋 I'm your **SQL Analytics Agent**.\n\n"
            "Ask me questions in plain English and I'll generate BigQuery SQL, execute it, and "
            "explain the results with insights — e.g. *\"What were the top 10 selling products last quarter?\"*"
        ),
    },
]

AGENT_MAP: dict[str, dict] = {a["id"]: a for a in AGENTS}


# ── Session state bootstrap ───────────────────────────────────────────────────

def _init_state() -> None:
    defaults: dict = {
        "current_agent":    None,
        "chat_histories":   {a["id"]: [] for a in AGENTS},
        "gcp_projects":     [],
        "selected_project": None,
        "projects_loaded":  False,
        "github_repo":      "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_state()


# ── GCP project loader (cached 5 min) ────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _load_gcp_projects() -> list[dict]:
    from utils.gcp_auth import list_projects
    return list_projects()


# ── Stream dispatcher ─────────────────────────────────────────────────────────

def _get_stream(agent_id: str, prompt: str):
    """Return the correct streaming generator for *agent_id*."""
    project = st.session_state.get("selected_project") or ""
    repo    = st.session_state.get("github_repo") or ""

    if agent_id == "gcp_cost":
        from agents.gcp_cost_agent import stream_cost_analysis
        return stream_cost_analysis(prompt, project)

    if agent_id == "gcp_recommender":
        from agents.gcp_recommender_agent import stream_recommendations
        return stream_recommendations(prompt, project)

    if agent_id == "github":
        from agents.github_agent import stream_github_analysis
        return stream_github_analysis(prompt, repo=repo or None)

    if agent_id == "code_optimizer":
        from agents.code_optimizer_agent import stream_code_optimization
        return stream_code_optimization(prompt, project_id=project, github_repo=repo)

    if agent_id == "docs":
        from agents.rag_agent import stream_confluence
        return stream_confluence(prompt)

    if agent_id == "sql":
        from agents.sql_agent import stream_sql_analysis
        return stream_sql_analysis(prompt)

    def _unknown():
        yield "❓ Unknown agent."
    return _unknown()


# ── Home screen ───────────────────────────────────────────────────────────────

def _open_agent(agent_id: str, prefill: str = "") -> None:
    history = st.session_state.chat_histories[agent_id]
    if not history:
        history.append({"role": "assistant", "content": AGENT_MAP[agent_id]["welcome"]})
    if prefill:
        st.session_state[f"_prefill_{agent_id}"] = prefill
    st.session_state.current_agent = agent_id
    st.rerun()


def _render_tile(agent: dict) -> None:
    label = f"{agent['icon']}  **{agent['title']}** — {agent['subtitle']}\n\n{agent['desc']}"
    if st.button(label, key=f"tile_{agent['id']}", use_container_width=True):
        _open_agent(agent["id"])


def render_home() -> None:
    # Hero
    st.markdown(
        '<h1 class="ip-hero-title">🚀 Insight Pilot</h1>'
        '<p class="ip-hero-sub">AI-powered GCP intelligence & data platform</p>',
        unsafe_allow_html=True,
    )

    # Global search
    with st.container():
        st.markdown('<div class="ip-search-wrap">', unsafe_allow_html=True)
        with st.form("home_search", clear_on_submit=True, border=False):
            c1, c2 = st.columns([9, 1])
            with c1:
                query = st.text_input(
                    "search",
                    placeholder="🔍  Ask anything across all agents...",
                    label_visibility="collapsed",
                )
            with c2:
                submitted = st.form_submit_button("→", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted and query:
        from agents.router import route_to_agent
        agent_id = route_to_agent(query)
        _open_agent(agent_id, prefill=query)
        return

    # Tiles
    st.markdown('<p class="ip-section">☁️ Cloud Intelligence</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: _render_tile(AGENT_MAP["gcp_cost"])
    with c2: _render_tile(AGENT_MAP["gcp_recommender"])

    st.markdown('<p class="ip-section">🛠️ Developer Tools</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: _render_tile(AGENT_MAP["github"])
    with c2: _render_tile(AGENT_MAP["code_optimizer"])

    st.markdown('<p class="ip-section">📊 Data & Docs</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: _render_tile(AGENT_MAP["docs"])
    with c2: _render_tile(AGENT_MAP["sql"])


# ── Context controls ──────────────────────────────────────────────────────────

def _render_project_selector() -> None:
    if not st.session_state.projects_loaded:
        with st.spinner("Loading GCP projects via ADC…"):
            projects = _load_gcp_projects()
            st.session_state.gcp_projects    = projects
            st.session_state.projects_loaded = True
            if projects and not st.session_state.selected_project:
                # Prefer the project the user authenticated with (gcloud config / ADC)
                from utils.gcp_auth import get_current_project
                adc_project = get_current_project()
                ids = [p["project_id"] for p in projects]
                if adc_project and adc_project in ids:
                    st.session_state.selected_project = adc_project
                else:
                    st.session_state.selected_project = projects[0]["project_id"]

    projects = st.session_state.gcp_projects
    col_sel, col_btn = st.columns([5, 1])

    with col_sel:
        if projects:
            ids    = [p["project_id"] for p in projects]
            labels = [f"{p['display_name']}  ({p['project_id']})" for p in projects]
            cur    = st.session_state.selected_project
            idx    = ids.index(cur) if cur in ids else 0
            choice = st.selectbox(
                "GCP Project",
                labels,
                index=idx,
                key="proj_select",
                label_visibility="collapsed",
            )
            st.session_state.selected_project = ids[labels.index(choice)]
        else:
            st.warning(
                "⚠️ No projects found. Run `gcloud auth application-default login` to authenticate.",
                icon="🔐",
            )

    with col_btn:
        if st.button("🔄", key="refresh_proj", help="Refresh project list", use_container_width=True):
            _load_gcp_projects.clear()
            st.session_state.projects_loaded = False
            st.rerun()


def _render_github_controls() -> None:
    repo = st.text_input(
        "Repository",
        value=st.session_state.github_repo,
        placeholder="owner/repo  (e.g. microsoft/vscode)",
        key="gh_repo_input",
        label_visibility="collapsed",
    )
    st.session_state.github_repo = repo


# ── Agent chat screen ─────────────────────────────────────────────────────────

def render_agent(agent_id: str) -> None:
    agent   = AGENT_MAP[agent_id]
    history: list[dict] = st.session_state.chat_histories[agent_id]

    # Top navigation bar
    nav_l, nav_m, _ = st.columns([1, 7, 1])
    with nav_l:
        if st.button("← Back", key="back_btn"):
            st.session_state.current_agent = None
            st.rerun()
    with nav_m:
        st.markdown(
            f'<div class="ip-agent-bar">'
            f'<span style="font-size:1.5rem">{agent["icon"]}</span>'
            f'<div><div class="ip-title">{agent["title"]}</div>'
            f'<div class="ip-sub">{agent["subtitle"]}</div></div>'
            f'<span class="ip-dot"></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Context controls
    if agent["requires_project"]:
        _render_project_selector()
    if agent["requires_github"]:
        _render_github_controls()

    # Chat history
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Prefilled query (from global home search)
    prefill = st.session_state.pop(f"_prefill_{agent_id}", "")

    # Chat input
    user_prompt = st.chat_input(agent["placeholder"], key=f"ci_{agent_id}")
    prompt      = user_prompt or prefill

    if prompt:
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            status = st.empty()
            status.markdown(
                '<span class="ip-generating">⏹ Generating…</span>',
                unsafe_allow_html=True,
            )
            try:
                full_response = st.write_stream(_get_stream(agent_id, prompt))
            except Exception as exc:
                full_response = f"❌ **Error:** {exc}"
                st.error(full_response)
            finally:
                status.empty()

        history.append({"role": "assistant", "content": full_response})

    # Clear conversation button
    if history:
        _, clr_col = st.columns([10, 1])
        with clr_col:
            if st.button("🗑️", key="clear_chat", help="Clear conversation"):
                st.session_state.chat_histories[agent_id] = []
                st.rerun()


# ── Main router ───────────────────────────────────────────────────────────────

def main() -> None:
    agent = st.session_state.current_agent
    if agent:
        render_agent(agent)
    else:
        render_home()


main()