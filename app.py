"""
Kuku Promo Finder — Streamlit App
==================================
Interactive prototype: upload a microdrama script → get ranked promo recommendations
Or browse all 50 pre-analyzed episodes.
"""

import streamlit as st
import json
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts" / "I Married a Broken Soldier. He was a Duke"
OUTPUT_DIR = BASE_DIR / "raw_outputs"
JSON_PATH = OUTPUT_DIR / "all_promos.json"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kuku Promo Finder",
    page_icon="🎬",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0d0d1a; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; }
    .metric-box {
        background: rgba(233,69,96,0.15);
        border: 1px solid #e94560;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
        margin: 4px;
    }
    .promo-rank {
        font-size: 28px;
        font-weight: 900;
        color: #ffd700;
    }
    .ts-badge {
        background: #1a1a3e;
        border: 1px solid #4444aa;
        border-radius: 6px;
        padding: 4px 10px;
        font-family: monospace;
        font-size: 15px;
        display: inline-block;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## 🎬")
with col_title:
    st.title("Kuku Promo Finder")
    st.caption("AI-powered promo identification for microdrama — *I Married a Broken Soldier. He was a Duke*")

st.divider()

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    if not JSON_PATH.exists():
        return None
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

data = load_data()

def ts(sec):
    """Float seconds → MM:SS.ss string"""
    m = int(sec) // 60
    s = sec - m * 60
    return f"{m:02d}:{s:05.2f}"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📺 Show")
    st.markdown("**I Married a Broken Soldier. He was a Duke**")
    st.markdown("*Romance microdrama — 50 episodes*")
    if data:
        st.markdown(f"**{data.get('total_promos_found',0)} promo candidates** found")
        st.markdown(f"**{len(data.get('cross_episode_montages',[]))} cross-episode montages**")

    st.divider()
    st.header("🧮 Scoring Formula")
    st.markdown("""
    ```
    total =
      hook × 2
    + emotional × 1.5
    + cliffhanger × 2
    + standalone × 1
    ```
    Max = 65 (normalized to display)
    """)

    st.divider()
    st.header("🔑 Hook keywords")
    st.markdown("`slap` `grab` `gasp` `No!` `blood` `reveal` `violent` `explosion` `traitor` `poison`...")
    st.header("⚡ Cliffhanger keywords")
    st.markdown("`ominous swell` `cut to black` `door slams` `Impossible` `unanswered ?`...")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_all, tab_upload, tab_method = st.tabs([
    "🏆 Top Promos — All 50 Episodes",
    "📄 Analyze New Script",
    "📊 Methodology & Limitations"
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — Pre-analyzed results
# ═════════════════════════════════════════════════════════════════════════════
with tab_all:
    if not data:
        st.error("No pre-analyzed data found. Run `promo_finder.py` first.")
        st.stop()

    clips = sorted(data.get("single_clip_promos", []), key=lambda x: x["total_score"], reverse=True)
    montages = sorted(data.get("cross_episode_montages", []), key=lambda x: x["total_score"], reverse=True)

    # Controls
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        show_n = st.slider("Show top N promos", 1, 20, 10)
    with ctrl2:
        min_score = st.slider("Min score", 0, 50, 20)
    with ctrl3:
        ep_filter = st.text_input("Filter by episode #", "")

    filtered_clips = [c for c in clips if c["total_score"] >= min_score]
    if ep_filter.strip().isdigit():
        ep_num = int(ep_filter.strip())
        filtered_clips = [c for c in filtered_clips if c["episode_number"] == ep_num]
    filtered_clips = filtered_clips[:show_n]

    st.markdown(f"**{len(filtered_clips)} single-clip promos** matching filters")

    # Single-clip promos
    for i, c in enumerate(filtered_clips):
        ep = c["episode_number"]
        s_time = c["start_time"]
        e_time = c["end_time"]
        dur = c["duration"]
        score = c["total_score"]
        hook_sc = c.get("hook_score", 0)
        cliff_sc = c.get("cliffhanger_score", 0)
        em_sc = c.get("emotional_score", 0)
        sa_sc = c.get("standalone_score", 0)
        hook_desc = c.get("hook_description", "")
        cliff_desc = c.get("cliffhanger_description", "")
        why = c.get("why_it_works", "")

        label = f"#{i+1}  |  Episode {ep:02d}  |  {ts(s_time)} → {ts(e_time)}  ({dur:.0f}s)  |  Score: {score:.1f}"
        with st.expander(label, expanded=(i < 3)):
            left, right = st.columns([3, 2])

            with left:
                st.markdown(f"**Episode {ep:02d}** — Segments:")
                st.markdown(
                    f'<span class="ts-badge">{ts(s_time)}</span> → '
                    f'<span class="ts-badge">{ts(e_time)}</span>  '
                    f'<b>{dur:.0f}s</b>',
                    unsafe_allow_html=True
                )
                st.markdown(f"**🎯 Hook:** {hook_desc[:180]}")
                st.markdown(f"**⚡ Cliffhanger:** {cliff_desc[:180] or 'Visual tension / unresolved scene'}")
                if why:
                    st.success(f"✅ {why}")

            with right:
                sc1, sc2 = st.columns(2)
                sc1.metric("🎯 Hook", f"{hook_sc:.1f}/10")
                sc2.metric("⚡ Cliff", f"{cliff_sc:.1f}/10")
                sc1.metric("💔 Emotion", f"{em_sc:.2f}/10")
                sc2.metric("👁️ Standalone", f"{sa_sc:.1f}/10")
                pct = min(score / 50, 1.0)
                st.progress(pct, text=f"Total: {score:.1f} ({pct*100:.0f}%)")

                # Platform recommendation
                if dur <= 30:
                    plat = "🎵 TikTok (best fit)"
                elif dur <= 60:
                    plat = "📸 Instagram Reels / TikTok"
                else:
                    plat = "▶️ YouTube Shorts"
                st.markdown(f"**Post on:** {plat}")

    # Cross-episode montages
    st.divider()
    st.subheader("🎞️ Cross-Episode Montage Promos")
    st.caption("Ep(N) ending → Ep(N+1) opening — creates maximum FOMO")

    for i, m in enumerate(montages[:5]):
        eps = m.get("episodes", [])
        s1 = m.get("segment_1", {})
        s2 = m.get("segment_2", {})
        total_dur = m.get("total_duration", 30)
        score = m.get("total_score", 0)
        hook_desc = m.get("hook_description", "")
        cliff_desc = m.get("cliffhanger_description", "")

        label = f"Montage #{i+1}  |  Ep{eps}  |  {total_dur:.0f}s  |  Score: {score:.1f}"
        with st.expander(label, expanded=(i == 0)):
            left, right = st.columns([3, 2])
            with left:
                st.markdown("**Segment 1:**")
                st.markdown(
                    f'Episode **{s1.get("episode","")}**: '
                    f'<span class="ts-badge">{ts(s1.get("start",0))}</span> → '
                    f'<span class="ts-badge">{ts(s1.get("end",0))}</span>',
                    unsafe_allow_html=True
                )
                st.markdown("**Segment 2:**")
                st.markdown(
                    f'Episode **{s2.get("episode","")}**: '
                    f'<span class="ts-badge">{ts(s2.get("start",0))}</span> → '
                    f'<span class="ts-badge">{ts(s2.get("end",0))}</span>',
                    unsafe_allow_html=True
                )
                st.markdown(f"**🎯 Hook:** {hook_desc[:160]}")
                st.markdown(f"**⚡ Cliffhanger:** {cliff_desc[:160] or 'Episode bridge tension'}")
            with right:
                h = m.get("hook_score", 0)
                cl = m.get("cliffhanger_score", 0)
                em = m.get("emotional_score", 0)
                sa = m.get("standalone_score", 0)
                sc1, sc2 = st.columns(2)
                sc1.metric("Hook", f"{h:.1f}/10")
                sc2.metric("Cliff", f"{cl:.1f}/10")
                sc1.metric("Emotion", f"{em:.2f}/10")
                sc2.metric("Standalone", f"{sa:.1f}/10")
                st.progress(min(score/50, 1.0), text=f"Score: {score:.1f}")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — Analyze a new script
# ═════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.subheader("Analyze Any Episode Script")
    st.markdown("Upload a `.txt` script in Kuku's format, or pick one of the 50 pre-loaded episodes.")

    mode = st.radio("Input method", ["📂 Choose from pre-loaded episodes", "⬆️ Upload a script file"])

    if mode == "⬆️ Upload a script file":
        uploaded = st.file_uploader("Upload .txt script", type=["txt"])
        if uploaded:
            content = uploaded.read().decode("utf-8", errors="replace")
            ep_path = BASE_DIR / "raw_outputs" / "_temp_upload.txt"
            ep_path.write_text(content, encoding="utf-8")
        else:
            ep_path = None
    else:
        eps_files = sorted(SCRIPTS_DIR.glob("episode-*.txt")) if SCRIPTS_DIR.exists() else []
        if eps_files:
            choice = st.selectbox("Episode", [f.name for f in eps_files])
            ep_path = SCRIPTS_DIR / choice
        else:
            st.error("Scripts directory not found.")
            ep_path = None

    if ep_path and st.button("🔍 Find Promos", type="primary"):
        sys.path.insert(0, str(BASE_DIR))
        try:
            from promo_finder import PromoFinder
            with st.spinner("Analyzing..."):
                finder = PromoFinder()
                result = finder.analyze_episode(str(ep_path))
        except Exception:
            # Fallback: try the function-based API
            try:
                from promo_finder import analyze_single_episode
                with st.spinner("Analyzing..."):
                    result = analyze_single_episode(str(ep_path))
            except Exception as e:
                st.error(f"Could not import promo_finder: {e}")
                result = None

        if result:
            promos = result if isinstance(result, list) else result.get("promos", [])
            st.success(f"Found **{len(promos)} promo candidates**")
            for i, p in enumerate(sorted(promos, key=lambda x: x.get("total_score", 0), reverse=True)[:5]):
                score = p.get("total_score", 0)
                s_t = p.get("start_time", p.get("start_sec", 0))
                e_t = p.get("end_time", p.get("end_sec", 0))
                dur = e_t - s_t
                with st.expander(f"Promo #{i+1} | {ts(s_t)} → {ts(e_t)} ({dur:.0f}s) | Score: {score:.1f}", expanded=(i==0)):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.code(f"{ts(s_t)} → {ts(e_t)}")
                        st.info(p.get("hook_description", "—")[:200])
                        st.warning(p.get("cliffhanger_description", "Visual tension")[:200])
                    with c2:
                        st.metric("Hook", f"{p.get('hook_score',0):.1f}/10")
                        st.metric("Cliffhanger", f"{p.get('cliffhanger_score',0):.1f}/10")
                        st.metric("Emotional", f"{p.get('emotional_score',0):.2f}/10")
                        st.metric("Standalone", f"{p.get('standalone_score',0):.1f}/10")
        else:
            st.info("Run `python promo_finder.py` from the command line, then refresh this page.")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — Methodology
# ═════════════════════════════════════════════════════════════════════════════
with tab_method:
    st.subheader("How the Promo Finder Works")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### Step 1: Parse
        Each `.txt` script → list of timestamped **moments**:
        - `CAMERA` directions
        - `ACTION` beats
        - `DIALOGUE` lines (speaker + stage direction + text)
        - `SOUND FX` cues

        ### Step 2: Slide
        2-second-step window slides over all 20–60s windows.
        Each window gets 4 scores.

        ### Step 3: Score
        ```
        hook_score        (0-10)  → first 3 seconds
        emotional_score   (0-10)  → avg window
        cliffhanger_score (0-10)  → last 5 seconds
        standalone_score  (0-10)  → clarity without prior eps

        total = hook×2 + emotional×1.5 + cliff×2 + standalone×1
        ```

        ### Step 4: Dedup
        Keep best non-overlapping window per episode (max 5).

        ### Step 5: Cross-episode
        Ep(N) last 15s + Ep(N+1) first 15s → montage promos.
        """)

    with col_b:
        st.markdown("""
        ### Known Limitations

        **Cliffhanger detection is weak.**
        Many cliffhangers are visual (slow zoom on a face) with no keywords.
        7 of top 10 promos score 0.0 on cliffhanger — this is an *undercount*.

        **Emotional score is low.**
        ~60% of each script is `CAMERA`/`ACTION` description,
        not dialogue. The emotional scorer finds fewer signals.

        **No visual quality signal.**
        Lighting, shot composition, and face expressiveness
        can only be measured by running the actual video frames
        through a vision model.

        ### What to do next
        - Add GPT-4V / Gemini Vision re-ranking on top 20 candidates
        - Connect to Kuku's video timeline tool to auto-mark in/out points
        - Run A/B tests on posted promos → update keyword weights

        ### Runtime
        | Input | Time |
        |-------|------|
        | 50 episodes | ~3 seconds |
        | 500 episodes | ~30 seconds |
        | 5,000 episodes | ~5 minutes |
        """)

    if data:
        st.divider()
        st.subheader("Analysis Statistics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Promos", data.get("total_promos_found", 0))
        m2.metric("Episodes", data.get("total_episodes_processed", 50))
        clips2 = data.get("single_clip_promos", [])
        top10_avg = sum(c["total_score"] for c in sorted(clips2, key=lambda x: x["total_score"], reverse=True)[:10]) / 10 if clips2 else 0
        m3.metric("Avg Score (top 10)", f"{top10_avg:.1f}")
        m4.metric("Cross-ep Montages", len(data.get("cross_episode_montages", [])))

st.divider()
st.caption("Kuku AI Generalist Assignment · Problem 1: Find the Promos · Built with Python + Streamlit · No API cost")
