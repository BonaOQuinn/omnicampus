"""
OmniCampus — Streamlit UI
Three tabs:
  1. Chat with Agents    — dedicated chat per agent
  2. Parallel Query      — broadcast one question to all three simultaneously
  3. Omnara Dashboard    — architecture, instance IDs, HITL explanation
"""
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

from agents.advising_agent import AdvisingAgent
from agents.finaid_agent import FinAidAgent
from agents.wellness_agent import WellnessAgent

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OmniCampus",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
AGENTS = {
    "Advising": AdvisingAgent(),
    "FinAid": FinAidAgent(),
    "Wellness": WellnessAgent(),
}

AGENT_META = {
    "Advising": {"icon": "📚", "color": "#4A90D9"},
    "FinAid":   {"icon": "💰", "color": "#27AE60"},
    "Wellness": {"icon": "🧠", "color": "#8E44AD"},
}

for key in ["chat_advising", "chat_finaid", "chat_wellness"]:
    if key not in st.session_state:
        st.session_state[key] = []

if "parallel_results" not in st.session_state:
    st.session_state.parallel_results = {}

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def render_sources(sources: list[str]) -> None:
    if sources:
        st.markdown("**Sources:**")
        cols = st.columns(min(len(sources), 4))
        for i, src in enumerate(sources):
            label = src.split("/")[-1] or src
            cols[i % 4].markdown(
                f"<span style='background:#f0f2f6;padding:2px 8px;"
                f"border-radius:12px;font-size:0.75em'>{label}</span>",
                unsafe_allow_html=True,
            )


def render_hitl_badge(result: dict) -> None:
    if result.get("hitl_triggered"):
        st.warning(
            f"🔔 HITL triggered — supervisor notified via Omnara.  "
            f"Reply: *\"{result.get('supervisor_reply') or 'pending'}\"*"
        )


def query_agent(agent_name: str, question: str) -> dict:
    return AGENTS[agent_name].answer(question)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style='text-align:center;padding:1rem 0 0.5rem'>
      <h1 style='margin:0'>🎓 OmniCampus</h1>
      <p style='color:#666;margin:0'>
        Parallel AI agents for CSU students · Powered by AWS Bedrock + Omnara
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(
    ["💬 Chat with Agents", "⚡ Parallel Query", "📡 Omnara Dashboard"]
)

# ===========================================================================
# TAB 1 — Chat with Agents
# ===========================================================================
with tab1:
    st.markdown("#### Chat with a specialist agent")
    col_adv, col_fin, col_wel = st.columns(3)

    def render_chat_column(col, agent_name: str, history_key: str):
        meta = AGENT_META[agent_name]
        with col:
            st.markdown(
                f"<h4 style='color:{meta['color']}'>"
                f"{meta['icon']} {agent_name} Agent"
                f"<br><small style='color:#999;font-size:0.6em'>"
                f"ID: {AGENTS[agent_name].instance_id}</small></h4>",
                unsafe_allow_html=True,
            )

            # Message history
            for msg in st.session_state[history_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant":
                        render_sources(msg.get("sources", []))
                        render_hitl_badge(msg)

            # Input
            prompt = st.chat_input(
                f"Ask the {agent_name} agent...",
                key=f"input_{agent_name.lower()}",
            )
            if prompt:
                st.session_state[history_key].append(
                    {"role": "user", "content": prompt}
                )
                with st.spinner(f"{meta['icon']} Thinking..."):
                    result = query_agent(agent_name, prompt)

                assistant_msg = {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "hitl_triggered": result["hitl_triggered"],
                    "supervisor_reply": result.get("supervisor_reply"),
                }
                st.session_state[history_key].append(assistant_msg)
                st.rerun()

    render_chat_column(col_adv, "Advising", "chat_advising")
    render_chat_column(col_fin, "FinAid",   "chat_finaid")
    render_chat_column(col_wel, "Wellness", "chat_wellness")

# ===========================================================================
# TAB 2 — Parallel Query
# ===========================================================================
with tab2:
    st.markdown(
        "#### Broadcast one question to all three agents simultaneously"
    )
    st.caption(
        "All agents fire in parallel — total time equals the *slowest* agent, "
        "not the sum of all three."
    )

    broadcast_q = st.text_input(
        "Your question",
        placeholder="e.g. I'm struggling with tuition costs and keeping up with classes",
        key="broadcast_input",
    )

    if st.button("⚡ Broadcast to All Agents", type="primary"):
        if broadcast_q.strip():
            progress = st.progress(0, text="Launching agents...")
            status_text = st.empty()
            completed = 0
            results = {}

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(query_agent, name, broadcast_q): name
                    for name in AGENTS
                }
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                    except Exception as exc:
                        results[name] = {
                            "agent": name,
                            "answer": f"Error: {exc}",
                            "sources": [],
                            "hitl_triggered": False,
                            "supervisor_reply": None,
                        }
                    completed += 1
                    pct = int(completed / len(AGENTS) * 100)
                    progress.progress(pct, text=f"{name} agent completed ({completed}/3)")
                    status_text.markdown(f"✅ **{name}** answered")

            progress.progress(100, text="All agents done!")
            st.session_state.parallel_results = results
        else:
            st.warning("Please enter a question first.")

    # Show results
    if st.session_state.parallel_results:
        st.divider()
        st.markdown("#### Results")
        cols = st.columns(3)
        for i, (agent_name, result) in enumerate(
            st.session_state.parallel_results.items()
        ):
            meta = AGENT_META[agent_name]
            with cols[i]:
                st.markdown(
                    f"<h5 style='color:{meta['color']}'>"
                    f"{meta['icon']} {agent_name}</h5>",
                    unsafe_allow_html=True,
                )
                st.markdown(result["answer"])
                render_sources(result["sources"])
                render_hitl_badge(result)

# ===========================================================================
# TAB 3 — Omnara Dashboard
# ===========================================================================
with tab3:
    st.markdown("#### Omnara Command Center")

    col_info, col_ids = st.columns([2, 1])

    with col_info:
        st.markdown(
            """
**OmniCampus** streams every agent action — question received, retrieval
started, answer generated, HITL triggered — to the
[Omnara](https://omnara.ai) web and mobile dashboard in real time.

##### Human-in-the-Loop (HITL)
When any agent detects a sensitive keyword (crisis, specific dollar amounts,
appeals), it pauses and sends a **push notification** to the designated
campus supervisor via Omnara. The supervisor reads the student's exact
question, types a reply from their phone, and the agent resumes with that
guidance. No terminal access required.

##### Architecture
```
Student (Streamlit UI)
        ↓
OmniCampus Orchestrator  (Python ThreadPoolExecutor)
        ↓ parallel
┌──────────────────────────────────────────┐
│  📚 Advising   💰 FinAid   🧠 Wellness  │
│     Agent        Agent       Agent       │
└──────┬───────────┬──────────┬────────────┘
       ↓           ↓          ↓
  Bedrock KB   Bedrock KB  Bedrock KB
 (S3:Catalog)  (S3:Aid)   (S3:Wellness)
       ↓           ↓          ↓
  Haiku 4.5  Haiku 4.5  Haiku 4.5
        ↓           ↓          ↓
┌──────────────────────────────────────────┐
│        Omnara Command Center             │
│ Live stream · HITL · Push Notifications  │
└──────────────────────────────────────────┘
```
            """
        )

    with col_ids:
        st.markdown("##### Live Agent Instance IDs")
        for agent_name, agent in AGENTS.items():
            meta = AGENT_META[agent_name]
            st.markdown(
                f"<div style='background:{meta['color']}22;"
                f"border-left:4px solid {meta['color']};"
                f"padding:8px 12px;border-radius:4px;margin-bottom:8px'>"
                f"<strong>{meta['icon']} {agent_name}</strong><br>"
                f"<code style='font-size:0.8em'>{agent.instance_id}</code>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown("##### Stack")
        st.markdown(
            "- **LLM:** Claude Haiku 4.5 (Bedrock)\n"
            "- **RAG:** Bedrock Knowledge Bases\n"
            "- **Vectors:** Amazon OpenSearch Serverless\n"
            "- **Embeddings:** Titan Embed Text v2\n"
            "- **Storage:** Amazon S3\n"
            "- **Orchestration:** ThreadPoolExecutor\n"
            "- **Monitoring:** Omnara SDK\n"
            "- **Frontend:** Streamlit"
        )

    st.divider()
    st.info(
        "**Demo tip:** Use the Parallel Query tab to broadcast *\"I'm struggling "
        "with tuition and keeping up with classes\"* — this triggers HITL on the "
        "Wellness agent and you'll see a push notification on the Omnara mobile app.",
        icon="💡",
    )
