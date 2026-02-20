"""
app.py  —  ARIA · Adaptive Role Intelligence Assistant
────────────────────────────────────────────────────────
• No pre-loaded roadmap or projects
• ARIA learns the user through natural conversation
• Profile, roadmap, projects & tasks are built dynamically
• Persisted to aria_profile.json (session + disk)
"""

import streamlit as st
import requests
import json
import re
import os
from datetime import datetime
from pathlib import Path
from aria_system import PERSONAS, EMPTY_PROFILE, build_system_prompt

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
PROFILE_PATH = Path("aria_profile.json")
OLLAMA_DEFAULT_URL = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "llama3.2"

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ARIA · Agentic AI Career Guide",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg:        #07090F;
    --bg-card:   #0C1020;
    --bg-raised: #121828;
    --border:    #1A2238;
    --text:      #D8DEEE;
    --muted:     #4E5870;
    --cyan:      #00D4FF;
    --purple:    #8B5CF6;
    --green:     #10F5A0;
    --orange:    #F59E0B;
    --pink:      #F472B6;
    --red:       #F87171;
    --blue:      #4F8EF7;
    --yellow:    #FBBF24;
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #05070D !important;
    border-right: 1px solid var(--border) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.1rem !important; }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── Header ── */
.aria-hdr {
    display: flex; align-items: center; gap: 18px;
    background: linear-gradient(120deg,#0A0F1E,#0D1528,#0A0F1E);
    border: 1px solid var(--border); border-top: 2px solid var(--cyan);
    border-radius: 14px; padding: 16px 24px; margin-bottom: 16px;
    position: relative; overflow: hidden;
}
.aria-hdr::after {
    content:''; position:absolute; top:-40%; left:-5%;
    width:50%; height:180%;
    background: radial-gradient(ellipse,rgba(0,212,255,.05),transparent 70%);
    pointer-events:none;
}
.aria-wm {
    font-family:'Space Mono',monospace; font-size:2rem; font-weight:700;
    color:var(--cyan); text-shadow:0 0 24px rgba(0,212,255,.4);
    letter-spacing:-2px; line-height:1; flex-shrink:0;
}
.aria-sub { font-size:.92rem; font-weight:600; color:var(--text); margin-bottom:2px; }
.aria-tag {
    font-family:'Space Mono',monospace; font-size:.6rem;
    color:var(--muted); text-transform:uppercase; letter-spacing:1.5px;
}
.live-dot {
    display:inline-block; width:7px; height:7px; background:var(--green);
    border-radius:50%; box-shadow:0 0 7px var(--green);
    animation:blink 2s ease-in-out infinite; vertical-align:middle; margin-right:5px;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background:transparent !important; gap:4px;
    border-bottom:1px solid var(--border) !important;
}
[data-testid="stTabs"] button {
    font-family:'Space Mono',monospace !important; font-size:.66rem !important;
    text-transform:uppercase !important; letter-spacing:1.2px !important;
    color:var(--muted) !important; padding:8px 16px !important;
    background:transparent !important; border:none !important;
    border-radius:8px 8px 0 0 !important; transition:color .2s !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color:var(--cyan) !important;
    border-bottom:2px solid var(--cyan) !important;
}

/* ── Cards ── */
.card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:12px; padding:16px 20px; margin-bottom:12px;
}

/* ── Section label ── */
.sl {
    font-family:'Space Mono',monospace; font-size:.58rem; color:var(--muted);
    text-transform:uppercase; letter-spacing:2px; margin-bottom:8px;
    padding-bottom:5px; border-bottom:1px solid var(--border);
}

/* ── Profile fields ── */
.pf-row {
    display:flex; align-items:baseline; gap:10px;
    padding: 6px 0; border-bottom:1px solid var(--border);
}
.pf-key {
    font-family:'Space Mono',monospace; font-size:.65rem; color:var(--muted);
    text-transform:uppercase; letter-spacing:.8px; min-width:120px; flex-shrink:0;
}
.pf-val { font-size:.82rem; color:var(--text); }
.pf-empty { font-size:.78rem; color:var(--border); font-style:italic; }

/* ── Persona pill ── */
.ppill {
    display:inline-flex; align-items:center; gap:7px;
    background:var(--bg-raised); border:1px solid var(--border);
    border-radius:20px; padding:5px 12px; font-size:.74rem;
    font-family:'Space Mono',monospace; margin-bottom:10px;
}
.pdot { width:7px;height:7px;border-radius:50%;flex-shrink:0; }

/* ── Status bar ── */
.oll-ok  { background:rgba(16,245,160,.07);border:1px solid rgba(16,245,160,.25);color:var(--green); }
.oll-err { background:rgba(248,113,113,.07);border:1px solid rgba(248,113,113,.25);color:var(--red); }
.oll-badge {
    display:flex;align-items:center;gap:8px;padding:7px 12px;
    border-radius:8px;font-size:.7rem;font-family:'Space Mono',monospace;margin-bottom:10px;
}

/* ── Metric ── */
.mbox {
    background:var(--bg-card);border:1px solid var(--border);
    border-radius:10px;padding:12px;text-align:center;
}
.mval {
    font-family:'Space Mono',monospace;font-size:1.5rem;
    font-weight:700;color:var(--cyan);line-height:1;
}
.mlbl {
    font-family:'Space Mono',monospace;font-size:.58rem;
    text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-top:4px;
}

/* ── Progress ── */
.prog-out { background:var(--border);border-radius:4px;height:4px;overflow:hidden; }
.prog-in  { height:100%;border-radius:4px;background:linear-gradient(90deg,var(--cyan),var(--purple)); }

/* ── Buttons ── */
.stButton > button {
    background:var(--bg-raised) !important; color:var(--text) !important;
    border:1px solid var(--border) !important; border-radius:8px !important;
    font-family:'Space Mono',monospace !important; font-size:.66rem !important;
    text-transform:uppercase !important; letter-spacing:.8px !important;
    padding:7px 14px !important; transition:all .2s !important;
}
.stButton > button:hover {
    border-color:var(--cyan) !important; color:var(--cyan) !important;
    box-shadow:0 0 10px rgba(0,212,255,.1) !important;
}

/* ── Chat ── */
[data-testid="stChatMessage"] { background:transparent !important; padding:4px 0 !important; }
[data-testid="stChatInput"] > div {
    background:var(--bg-card) !important; border:1px solid var(--border) !important; border-radius:12px !important;
}
[data-testid="stChatInput"] textarea {
    background:transparent !important; color:var(--text) !important;
    font-family:'DM Sans',sans-serif !important; font-size:.9rem !important;
}

/* ── Roadmap phase card ── */
.phase-card {
    background:var(--bg-card); border:1px solid var(--border); border-radius:12px;
    padding:14px 18px; margin-bottom:10px; position:relative;
}
.phase-card.active { border-left:3px solid var(--green); background:linear-gradient(135deg,rgba(16,245,160,.04),var(--bg-card)); }
.phase-card.done   { border-left:3px solid var(--blue); opacity:.8; }
.phase-card.locked { opacity:.45; }
.phase-num {
    font-family:'Space Mono',monospace; font-size:.58rem; color:var(--muted);
    text-transform:uppercase; letter-spacing:1px; margin-bottom:2px;
}
.phase-title { font-size:.95rem; font-weight:700; color:var(--text); margin-bottom:6px; }

/* ── Project card ── */
.proj-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:12px; padding:16px 20px; margin-bottom:10px;
}
.proj-name { font-size:1rem; font-weight:700; margin:3px 0 6px; }
.proj-desc { font-size:.8rem; color:#7A83A2; line-height:1.6; margin-bottom:8px; }
.proj-why  { font-size:.74rem; color:var(--muted); font-style:italic; margin-bottom:8px; }
.ttag {
    display:inline-block; background:var(--bg-raised); border:1px solid var(--border);
    border-radius:4px; padding:2px 8px; font-size:.62rem;
    font-family:'Space Mono',monospace; color:var(--muted); margin:2px 2px 0 0;
}

/* ── Task card ── */
.task-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:10px; padding:12px 16px; margin-bottom:8px;
    display:flex; gap:14px; align-items:flex-start;
}
.task-day {
    font-family:'Space Mono',monospace; font-size:.65rem; color:var(--cyan);
    text-transform:uppercase; min-width:40px; padding-top:2px;
}
.task-text { font-size:.82rem; color:var(--text); line-height:1.5; }
.task-meta { font-size:.7rem; color:var(--muted); margin-top:3px; font-family:'Space Mono',monospace; }

/* ── Banners ── */
.banner-info {
    background:rgba(0,212,255,.06); border:1px solid rgba(0,212,255,.2);
    border-radius:10px; padding:14px 18px; margin-bottom:14px; font-size:.83rem; color:#8ABED8;
}
.banner-warn {
    background:rgba(245,158,11,.06); border:1px solid rgba(245,158,11,.2);
    border-radius:10px; padding:14px 18px; margin-bottom:14px; font-size:.83rem; color:#C9A44A;
}
.banner-ok {
    background:rgba(16,245,160,.06); border:1px solid rgba(16,245,160,.2);
    border-radius:10px; padding:14px 18px; margin-bottom:14px; font-size:.83rem; color:#4AC98A;
}

/* ── Select/input ── */
[data-testid="stSelectbox"] > div,
[data-testid="stTextInput"] > div > div {
    background:var(--bg-card) !important; border:1px solid var(--border) !important;
    color:var(--text) !important; border-radius:8px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background:var(--bg-card) !important; border:1px solid var(--border) !important;
    border-radius:10px !important; margin-bottom:8px !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Profile persistence
# ─────────────────────────────────────────────────────────────────────────────
def load_profile() -> dict:
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH) as f:
                saved = json.load(f)
            # merge so new keys from EMPTY_PROFILE always present
            merged = {**EMPTY_PROFILE, **saved}
            return merged
        except Exception:
            pass
    return dict(EMPTY_PROFILE)


def save_profile(profile: dict):
    profile["last_updated"] = datetime.now().isoformat()
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def export_profile_json(profile: dict) -> str:
    return json.dumps(profile, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# Ollama helpers
# ─────────────────────────────────────────────────────────────────────────────
def check_ollama(url: str):
    try:
        r = requests.get(f"{url}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []


def stream_ollama(prompt: str, history: list, profile: dict, url: str, model: str):
    """Stream tokens from Ollama, yielding each token as a string."""
    system_prompt = build_system_prompt(profile)
    messages = [{"role": "system", "content": system_prompt}]
    for m in history[-16:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.72, "top_p": 0.9, "num_predict": 2048},
    }
    try:
        with requests.post(f"{url}/api/chat", json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines():
                if not raw:
                    continue
                chunk = json.loads(raw)
                tok = chunk.get("message", {}).get("content", "")
                if tok:
                    yield tok
                if chunk.get("done"):
                    break
    except requests.exceptions.ConnectionError:
        yield (
            "\n\n> ⚠️ **Ollama not reachable.**\n"
            "> Run: `ollama serve`  then  `ollama pull llama3.2`"
        )
    except Exception as exc:
        yield f"\n\n> ⚠️ **Error:** `{exc}`"

# ─────────────────────────────────────────────────────────────────────────────
# JSON extraction from ARIA responses
# ─────────────────────────────────────────────────────────────────────────────
def extract_json_block(text: str):
    """Pull the first ```json ... ``` block from a response and parse it."""
    match = re.search(r"```json\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def maybe_absorb_generated_data(response_text: str, profile: dict) -> bool:
    """
    If the response contains a JSON block that looks like roadmap / projects /
    weekly tasks, absorb it into the profile. Returns True if profile was changed.
    """
    data = extract_json_block(response_text)
    if data is None or not isinstance(data, list) or len(data) == 0:
        return False

    changed = False
    first = data[0]

    # Roadmap detection: items have 'phase' or 'weeks' + 'title'
    if isinstance(first, dict) and ("phase" in first or "weeks" in first) and "title" in first:
        profile["roadmap"] = data
        profile["current_phase"] = 0
        profile["completed_phases"] = []
        changed = True

    # Project detection: items have 'rank' and 'name' and 'tech'
    elif isinstance(first, dict) and "rank" in first and "name" in first and "tech" in first:
        profile["projects"] = data
        changed = True

    # Weekly tasks detection: items have 'day' and 'task'
    elif isinstance(first, dict) and "day" in first and "task" in first:
        profile["weekly_tasks"] = data
        changed = True

    return changed


# ─────────────────────────────────────────────────────────────────────────────
# Profile field extractor (heuristic, runs silently after every message)
# ─────────────────────────────────────────────────────────────────────────────
_LEVEL_KEYWORDS = {
    "beginner":     "beginner",
    "just started": "beginner",
    "new to":       "beginner",
    "intermediate": "intermediate",
    "some experience": "intermediate",
    "advanced":     "advanced",
    "experienced":  "advanced",
}
_EXPOSURE_KEYWORDS = {
    "never":        "none",
    "no experience":"none",
    "read about":   "theory_only",
    "watched":      "theory_only",
    "some projects":"some_projects",
    "built":        "some_projects",
    "deployed":     "some_projects",
}

def heuristic_profile_update(user_text: str, profile: dict) -> bool:
    """Lightweight keyword scan to auto-fill obvious profile fields."""
    changed = False
    lower = user_text.lower()

    # Python level
    if not profile["python_level"]:
        for kw, val in _LEVEL_KEYWORDS.items():
            if kw in lower and "python" in lower:
                profile["python_level"] = val
                changed = True
                break

    # AI exposure
    if not profile["ai_exposure"]:
        for kw, val in _EXPOSURE_KEYWORDS.items():
            if kw in lower and any(w in lower for w in ["ai", "ml", "machine learning", "deep learning"]):
                profile["ai_exposure"] = val
                changed = True
                break

    # Hours per week
    if not profile["time_per_week"]:
        m = re.search(r"(\d{1,2})\s*(hours?|hrs?)\s*(a|per)?\s*week", lower)
        if m:
            profile["time_per_week"] = int(m.group(1))
            changed = True

    # Mark diagnosis done when key fields are present
    if (not profile["diagnosis_done"]
            and profile["python_level"]
            and profile["ai_exposure"]):
        profile["diagnosis_done"] = True
        changed = True

    return changed


def detect_persona(text: str, current: str) -> str:
    lower = text.lower()
    for name, data in PERSONAS.items():
        if any(t in lower for t in data["triggers"]):
            return name
    return current

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    if "profile" not in st.session_state:
        st.session_state.profile = load_profile()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_persona" not in st.session_state:
        st.session_state.active_persona = "🧑‍🏫 Instructor"
    if "ollama_url" not in st.session_state:
        st.session_state.ollama_url = OLLAMA_DEFAULT_URL
    if "ollama_model" not in st.session_state:
        st.session_state.ollama_model = OLLAMA_DEFAULT_MODEL
    if "msg_count" not in st.session_state:
        st.session_state.msg_count = 0
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "aria_greeted" not in st.session_state:
        st.session_state.aria_greeted = False

init_state()
profile = st.session_state.profile

# ─────────────────────────────────────────────────────────────────────────────
# Core send-message logic
# ─────────────────────────────────────────────────────────────────────────────
def send_message(user_text: str):
    p = st.session_state.profile

    # Detect persona
    st.session_state.active_persona = detect_persona(user_text, st.session_state.active_persona)

    # Heuristic profile update from user text
    if heuristic_profile_update(user_text, p):
        save_profile(p)

    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.msg_count += 1

    with st.chat_message("user"):
        st.markdown(user_text)

    # Stream ARIA response
    with st.chat_message("assistant"):
        box = st.empty()
        full = ""
        for tok in stream_ollama(
            user_text,
            st.session_state.messages[:-1],
            p,
            st.session_state.ollama_url,
            st.session_state.ollama_model,
        ):
            full += tok
            box.markdown(full + "▌")
        box.markdown(full)

    # Absorb any generated JSON (roadmap / projects / tasks)
    if maybe_absorb_generated_data(full, p):
        save_profile(p)

    st.session_state.messages.append({"role": "assistant", "content": full})
    st.session_state.msg_count += 1


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 20px;">
      <div style="font-family:'Space Mono',monospace;font-size:1.85rem;font-weight:700;
                  color:#00D4FF;text-shadow:0 0 20px rgba(0,212,255,.4);letter-spacing:-2px;">ARIA</div>
      <div style="font-size:.57rem;color:#4E5870;font-family:'Space Mono',monospace;
                  letter-spacing:2px;text-transform:uppercase;margin-top:3px;">
        Agentic AI Career Guide
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Ollama
    ok, avail = check_ollama(st.session_state.ollama_url)
    cls = "oll-ok" if ok else "oll-err"
    lbl = f"Ollama · {len(avail)} model(s)" if ok else "Ollama offline — ollama serve"
    st.markdown(f'<div class="oll-badge {cls}">⬤ {lbl}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sl">Model</div>', unsafe_allow_html=True)
    if avail:
        idx = avail.index(st.session_state.ollama_model) if st.session_state.ollama_model in avail else 0
        st.session_state.ollama_model = st.selectbox("model", avail, index=idx, label_visibility="collapsed")
    else:
        st.session_state.ollama_model = st.text_input(
            "model_txt", value=st.session_state.ollama_model,
            placeholder="e.g. llama3.2", label_visibility="collapsed"
        )
        st.caption("`ollama pull llama3.2`")

    st.divider()

    # Active persona
    st.markdown('<div class="sl">Active Persona</div>', unsafe_allow_html=True)
    ap = st.session_state.active_persona
    pd_data = PERSONAS[ap]
    emoji_p = ap.split(" ")[0]
    name_p  = " ".join(ap.split(" ")[1:])
    st.markdown(f"""
    <div class="ppill" style="border-color:{pd_data['color']}33;">
      <div class="pdot" style="background:{pd_data['color']};box-shadow:0 0 6px {pd_data['color']};"></div>
      <div>
        <div style="font-size:.78rem;font-weight:600;">{emoji_p} {name_p}</div>
        <div style="font-size:.61rem;color:#4E5870;">{pd_data['desc']}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="font-size:.58rem;color:#4E5870;font-family:Space Mono,monospace;'
                'margin-bottom:5px;text-transform:uppercase;letter-spacing:1px;">Override</div>',
                unsafe_allow_html=True)
    for pn in PERSONAS:
        if st.button(pn, key=f"pb_{pn}", use_container_width=True):
            st.session_state.active_persona = pn
            st.rerun()

    st.divider()

    # Stats
    st.markdown('<div class="sl">Session</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="mbox"><div class="mval">{st.session_state.msg_count}</div>'
                    f'<div class="mlbl">Msgs</div></div>', unsafe_allow_html=True)
    with c2:
        ph_total = len(profile.get("roadmap", []))
        ph_done  = len(profile.get("completed_phases", []))
        disp = f"{ph_done}/{ph_total}" if ph_total else "—"
        st.markdown(f'<div class="mbox"><div class="mval">{disp}</div>'
                    f'<div class="mlbl">Phases</div></div>', unsafe_allow_html=True)

    st.divider()

    # Quick prompts
    st.markdown('<div class="sl">Quick Prompts</div>', unsafe_allow_html=True)
    QUICK = {
        "📋 Generate My Roadmap":
            "Based on everything you know about me so far, generate my personalized roadmap now. "
            "Output it as a JSON block following the schema you've been given.",
        "🚀 Suggest My Projects":
            "Based on my current level, suggest 3 portfolio projects for me. "
            "Output them as a JSON block following the schema you've been given.",
        "📅 This Week's Tasks":
            "Generate my weekly tasks for my current phase. "
            "Output them as a JSON block following the schema you've been given.",
        "⚡ Challenge Me":
            "Give me a coding challenge appropriate for my exact current level right now.",
        "🗺️ Career Advice":
            "Give me honest, specific career advice for becoming an Agentic AI developer in 2025. "
            "Tell me what skills matter most and what my GitHub needs to look like.",
        "💾 Export My Profile":
            "__export__",
        "🗑️ Reset Everything":
            "__reset__",
    }
    for label, action in QUICK.items():
        if st.button(label, key=f"qp_{label}", use_container_width=True):
            if action == "__export__":
                st.download_button(
                    "⬇️ Download JSON",
                    data=export_profile_json(profile),
                    file_name="aria_profile.json",
                    mime="application/json",
                    key="dl_profile",
                )
            elif action == "__reset__":
                if PROFILE_PATH.exists():
                    PROFILE_PATH.unlink()
                for k in ["profile","messages","msg_count","aria_greeted","active_persona","pending_prompt"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
            else:
                st.session_state.pending_prompt = action
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="aria-hdr">
  <div class="aria-wm">ARIA</div>
  <div>
    <div class="aria-sub">Adaptive Role Intelligence Assistant</div>
    <div class="aria-tag"><span class="live-dot"></span>Learning your profile · Powered by Ollama (local)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_chat, tab_profile, tab_road, tab_proj, tab_tasks = st.tabs([
    "💬  CHAT  ",
    "👤  MY PROFILE  ",
    "🗺️  ROADMAP  ",
    "🚀  PROJECTS  ",
    "📅  THIS WEEK  ",
])

# ══════════════════════════════════════════════════════════════════════════════
# CHAT TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    # First-launch auto-greeting
    if not st.session_state.aria_greeted and not st.session_state.messages:
        st.session_state.aria_greeted = True
        greeting_prompt = (
            "Please introduce yourself and begin getting to know me naturally through conversation."
        )
        send_message(greeting_prompt)
        st.rerun()

    # Render history (skip the hidden greeting trigger)
    display_messages = st.session_state.messages
    # Hide first user message (it was the internal greeting trigger)
    if display_messages and display_messages[0]["role"] == "user":
        display_messages = display_messages[1:]

    for msg in display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Pending prompt from sidebar
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        send_message(prompt)
        st.rerun()

    # Chat input
    if user_in := st.chat_input("Talk to ARIA — anything on your mind…"):
        send_message(user_in)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_profile:
    st.markdown("""
    <div style="margin-bottom:18px;">
      <div class="sl">Your Learner Profile</div>
      <p style="color:#4E5870;font-size:.82rem;margin:0;">
        ARIA builds this automatically from your conversation.
        The richer your answers, the more personalised your guidance becomes.
      </p>
    </div>
    """, unsafe_allow_html=True)

    if not profile.get("diagnosis_done"):
        st.markdown("""
        <div class="banner-info">
          🔍 <strong>Profile in progress</strong> — ARIA is still learning about you.
          Keep chatting and it will fill in automatically. Once your Python level and
          AI exposure are known, ARIA will offer to generate your roadmap.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="banner-ok">
          ✅ <strong>Profile complete</strong> — ARIA knows your level. Use the sidebar prompts
          to generate your personalised roadmap and project suggestions.
        </div>
        """, unsafe_allow_html=True)

    # Profile display
    fields = [
        ("Name",             profile.get("name")),
        ("Python Level",     profile.get("python_level")),
        ("AI/ML Exposure",   profile.get("ai_exposure")),
        ("Tools Known",      ", ".join(profile.get("current_tools", [])) or None),
        ("Career Goal",      profile.get("career_goal")),
        ("Hours / Week",     f"{profile.get('time_per_week')} hrs" if profile.get("time_per_week") else None),
        ("Strengths",        ", ".join(profile.get("strengths", [])) or None),
        ("Known Gaps",       ", ".join(profile.get("gaps", [])) or None),
        ("Roadmap Phases",   str(len(profile.get("roadmap", []))) + " phases" if profile.get("roadmap") else None),
        ("Projects",         str(len(profile.get("projects", []))) + " suggested" if profile.get("projects") else None),
        ("Last Updated",     profile.get("last_updated")),
    ]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    for key, val in fields:
        val_html = f'<span class="pf-val">{val}</span>' if val else '<span class="pf-empty">not yet known</span>'
        st.markdown(
            f'<div class="pf-row"><span class="pf-key">{key}</span>{val_html}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Manual overrides
    with st.expander("✏️ Edit profile manually"):
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Your name", value=profile.get("name") or "")
            new_py   = st.selectbox("Python level",
                                    ["", "beginner", "intermediate", "advanced"],
                                    index=["", "beginner", "intermediate", "advanced"].index(
                                        profile.get("python_level") or ""))
            new_ai = st.selectbox("AI/ML exposure",
                                  ["", "none", "theory_only", "some_projects"],
                                  index=["", "none", "theory_only", "some_projects"].index(
                                      profile.get("ai_exposure") or ""))
        with c2:
            new_hrs  = st.number_input("Hours/week", min_value=0, max_value=80,
                                       value=int(profile.get("time_per_week") or 0))
            new_goal = st.text_area("Career goal", value=profile.get("career_goal") or "", height=80)

        if st.button("💾 Save Changes", use_container_width=True):
            if new_name:  profile["name"]          = new_name
            if new_py:    profile["python_level"]   = new_py
            if new_ai:    profile["ai_exposure"]    = new_ai
            if new_hrs:   profile["time_per_week"]  = new_hrs
            if new_goal:  profile["career_goal"]    = new_goal
            if new_py and new_ai:
                profile["diagnosis_done"] = True
            save_profile(profile)
            st.success("Profile saved!")
            st.rerun()

    # Export
    st.divider()
    st.download_button(
        "⬇️ Export Full Profile as JSON",
        data=export_profile_json(profile),
        file_name="aria_profile.json",
        mime="application/json",
    )


# ══════════════════════════════════════════════════════════════════════════════
# ROADMAP TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_road:
    roadmap = profile.get("roadmap", [])

    st.markdown("""
    <div style="margin-bottom:16px;">
      <div class="sl">Your Personalised Roadmap</div>
      <p style="color:#4E5870;font-size:.82rem;margin:0;">
        Generated by ARIA from your actual profile — not a generic template.
      </p>
    </div>
    """, unsafe_allow_html=True)

    if not roadmap:
        st.markdown("""
        <div class="banner-warn">
          🗺️ <strong>No roadmap yet.</strong>
          Once ARIA knows your level, click <em>"📋 Generate My Roadmap"</em> in the sidebar
          (or just ask ARIA in chat). It will be built specifically for you.
        </div>
        """, unsafe_allow_html=True)

        if profile.get("diagnosis_done"):
            if st.button("📋 Generate My Roadmap Now", use_container_width=True):
                st.session_state.pending_prompt = (
                    "Based on everything you know about me so far, generate my personalized roadmap now. "
                    "Output it as a JSON block following the schema you've been given."
                )
                st.rerun()
        else:
            st.markdown("""
            <div class="banner-info">
              💬 <strong>First, chat with ARIA.</strong>
              Go to the Chat tab and answer a few questions so ARIA can learn your level.
            </div>
            """, unsafe_allow_html=True)
    else:
        current_idx = profile.get("current_phase", 0)
        done_phases = profile.get("completed_phases", [])
        total = len(roadmap)
        pct   = int((len(done_phases) / total) * 100) if total else 0

        # Progress bar
        st.markdown(f"""
        <div class="card" style="margin-bottom:18px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-family:'Space Mono',monospace;font-size:.66rem;color:#4E5870;
                         text-transform:uppercase;letter-spacing:1px;">Overall Progress</span>
            <span style="font-family:'Space Mono',monospace;font-size:.8rem;color:#00D4FF;font-weight:700;">{pct}%</span>
          </div>
          <div class="prog-out"><div class="prog-in" style="width:{pct}%;"></div></div>
          <div style="font-size:.72rem;color:#4E5870;margin-top:7px;">
            {len(done_phases)} of {total} phases complete
          </div>
        </div>
        """, unsafe_allow_html=True)

        for i, phase in enumerate(roadmap):
            is_done   = i in done_phases or i < current_idx
            is_active = i == current_idx
            is_locked = not is_done and not is_active
            icon = "✅" if is_done else ("🔥" if is_active else "🔒")
            css  = "done" if is_done else ("active" if is_active else "locked")

            title    = phase.get("title", f"Phase {i+1}")
            weeks    = phase.get("weeks", "")
            topics   = phase.get("topics", [])
            milestone = phase.get("milestone", "")

            with st.expander(f"{icon}  Phase {i+1}  ·  {title}  {'· ' + weeks if weeks else ''}", expanded=is_active):
                col_t, col_m = st.columns([3, 2])
                with col_t:
                    if topics:
                        st.markdown("**Topics**")
                        for t in topics:
                            st.markdown(f"- {t}")
                with col_m:
                    if milestone:
                        st.markdown(f"""
                        <div style="background:#121828;border:1px solid #1A2238;border-radius:8px;padding:12px;">
                          <div style="font-family:'Space Mono',monospace;font-size:.58rem;color:#4E5870;
                                      text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;">🎯 Milestone</div>
                          <div style="font-size:.8rem;color:#D8DEEE;line-height:1.5;">{milestone}</div>
                        </div>""", unsafe_allow_html=True)

                if is_active:
                    a1, a2 = st.columns(2)
                    with a1:
                        if st.button("📅 Generate Week Tasks", key=f"wtask_{i}"):
                            st.session_state.pending_prompt = (
                                f"Generate my weekly tasks for Phase {i+1}: {title}. "
                                "Output them as a JSON block following the schema you've been given."
                            )
                            st.rerun()
                    with a2:
                        if st.button("📚 Teach This Phase", key=f"teach_{i}"):
                            st.session_state.pending_prompt = (
                                f"I'm starting Phase {i+1}: {title}. "
                                f"Topics: {', '.join(topics)}. "
                                "Give me a structured lesson plan for the first week. "
                                "Start with the very first thing I should do today."
                            )
                            st.rerun()

                    if st.button(f"✅ Mark Phase {i+1} Complete", key=f"done_{i}"):
                        if i not in profile["completed_phases"]:
                            profile["completed_phases"].append(i)
                        profile["current_phase"] = min(i + 1, total - 1)
                        save_profile(profile)
                        st.rerun()

        if st.button("🔄 Regenerate Roadmap", use_container_width=True):
            st.session_state.pending_prompt = (
                "Please regenerate my roadmap from scratch based on my current profile. "
                "Output it as a JSON block following the schema you've been given."
            )
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PROJECTS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_proj:
    projects = profile.get("projects", [])

    st.markdown("""
    <div style="margin-bottom:16px;">
      <div class="sl">Your Portfolio Projects</div>
      <p style="color:#4E5870;font-size:.82rem;margin:0;">
        ARIA suggests projects based on your actual skill level — not a generic list.
      </p>
    </div>
    """, unsafe_allow_html=True)

    if not projects:
        st.markdown("""
        <div class="banner-warn">
          🚀 <strong>No projects suggested yet.</strong>
          Click <em>"🚀 Suggest My Projects"</em> in the sidebar once ARIA knows your level,
          or ask directly in chat: <em>"suggest 3 portfolio projects for me"</em>.
        </div>
        """, unsafe_allow_html=True)
        if profile.get("diagnosis_done"):
            if st.button("🚀 Suggest Projects for My Level", use_container_width=True):
                st.session_state.pending_prompt = (
                    "Based on my current level, suggest 3 portfolio projects for me. "
                    "Output them as a JSON block following the schema you've been given."
                )
                st.rerun()
    else:
        cx_colors = {"Beginner": "#10F5A0", "Intermediate": "#4F8EF7", "Advanced": "#F472B6"}
        accent_colors = ["#4FF79E", "#4F8EF7", "#F74FA8"]

        for idx, proj in enumerate(projects):
            cc  = accent_colors[idx % len(accent_colors)]
            cxc = cx_colors.get(proj.get("complexity", ""), "#9CA3AF")
            tags = "".join(f'<span class="ttag">{t}</span>' for t in proj.get("tech", []))

            st.markdown(f"""
            <div class="proj-card" style="border-left:3px solid {cc};">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                <div>
                  <div style="font-family:'Space Mono',monospace;font-size:.58rem;color:#4E5870;margin-bottom:2px;">
                    #{proj.get('rank','?')} &nbsp;·&nbsp;
                    <span style="color:{cxc};">{proj.get('complexity','')}</span>
                  </div>
                  <div class="proj-name" style="color:{cc};">{proj.get('name','Project')}</div>
                </div>
              </div>
              <div class="proj-desc">{proj.get('description', proj.get('desc',''))}</div>
              <div class="proj-why">💡 {proj.get('why','')}</div>
              <div>{tags}</div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                if st.button(f"📋 Plan It", key=f"planp_{idx}", use_container_width=True):
                    st.session_state.pending_prompt = (
                        f"I want to build '{proj.get('name')}'. "
                        "Break it into phases with clear weekly goals. "
                        "List what I need to install and give me the first coding task to do today."
                    )
                    st.rerun()
            with b2:
                if st.button(f"🏗️ Architecture", key=f"archp_{idx}", use_container_width=True):
                    st.session_state.pending_prompt = (
                        f"Design the system architecture for '{proj.get('name')}'. "
                        "Include an ASCII data-flow diagram, explain each component, "
                        "and list all dependencies with install commands."
                    )
                    st.rerun()
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if st.button("🔄 Regenerate Project Suggestions", use_container_width=True):
            st.session_state.pending_prompt = (
                "Suggest 3 fresh portfolio projects based on my current level. "
                "Output them as a JSON block following the schema you've been given."
            )
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# THIS WEEK TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_tasks:
    tasks = profile.get("weekly_tasks", [])
    roadmap = profile.get("roadmap", [])
    current_idx = profile.get("current_phase", 0)

    st.markdown("""
    <div style="margin-bottom:16px;">
      <div class="sl">This Week's Action Plan</div>
      <p style="color:#4E5870;font-size:.82rem;margin:0;">
        ARIA generates specific daily tasks for your current phase,
        respecting your available hours per week.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Current phase context
    if roadmap and current_idx < len(roadmap):
        cp = roadmap[current_idx]
        st.markdown(f"""
        <div class="card" style="border-left:3px solid #10F5A0;margin-bottom:16px;">
          <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#4E5870;
                      text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Current Phase</div>
          <div style="font-size:.95rem;font-weight:700;color:#D8DEEE;">
            Phase {cp.get('phase', current_idx+1)} · {cp.get('title','')}
          </div>
          {f'<div style="font-size:.76rem;color:#4E5870;margin-top:3px;">Weeks: {cp.get("weeks","")}</div>' if cp.get('weeks') else ''}
        </div>
        """, unsafe_allow_html=True)

    if not tasks:
        st.markdown("""
        <div class="banner-warn">
          📅 <strong>No tasks generated yet.</strong>
          Click below to have ARIA plan your week, or use
          <em>"📅 This Week's Tasks"</em> in the sidebar.
        </div>
        """, unsafe_allow_html=True)

        can_gen = bool(roadmap) or profile.get("diagnosis_done")
        if can_gen:
            if st.button("📅 Generate This Week's Tasks", use_container_width=True):
                st.session_state.pending_prompt = (
                    "Generate my weekly tasks for my current learning phase. "
                    "Output them as a JSON block following the schema you've been given."
                )
                st.rerun()
        else:
            st.markdown("""
            <div class="banner-info">
              💬 <strong>Chat with ARIA first</strong> so it understands your level,
              then generate your roadmap, then come back here for weekly tasks.
            </div>
            """, unsafe_allow_html=True)
    else:
        # Total hours
        total_hrs = sum(float(t.get("estimated_hours", 1)) for t in tasks)
        avail_hrs = profile.get("time_per_week") or "?"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="mbox"><div class="mval">{len(tasks)}</div>'
                        f'<div class="mlbl">Tasks</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="mbox"><div class="mval">{total_hrs:.0f}h</div>'
                        f'<div class="mlbl">Est. Time</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="mbox"><div class="mval">{avail_hrs}h</div>'
                        f'<div class="mlbl">Your Budget</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        for t in tasks:
            day      = t.get("day", "")
            task_txt = t.get("task", "")
            resource = t.get("resource", "")
            est_hrs  = t.get("estimated_hours", "")

            meta_parts = []
            if est_hrs:   meta_parts.append(f"⏱ {est_hrs}h")
            if resource:  meta_parts.append(f"📖 {resource}")
            meta_html = " &nbsp;·&nbsp; ".join(meta_parts)

            st.markdown(f"""
            <div class="task-card">
              <div class="task-day">{day}</div>
              <div>
                <div class="task-text">{task_txt}</div>
                {f'<div class="task-meta">{meta_html}</div>' if meta_html else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔄 Regenerate Tasks", use_container_width=True):
                st.session_state.pending_prompt = (
                    "Generate a fresh set of weekly tasks for my current phase. "
                    "Output them as a JSON block following the schema you've been given."
                )
                st.rerun()
        with b2:
            if st.button("⚡ Challenge Me on These Topics", use_container_width=True):
                topics_str = ", ".join(t.get("task","")[:40] for t in tasks[:3])
                st.session_state.pending_prompt = (
                    f"Based on this week's tasks ({topics_str}), give me a coding challenge "
                    "I should work on right now to lock in my learning."
                )
                st.rerun()
