import streamlit as st
import os
import sys
import time
import threading
from io import StringIO
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT → Blog Generator",
    page_icon="📝",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0D0D0D;
    color: #F5F5F5;
  }

  .main { background-color: #0D0D0D; }

  h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
  }

  /* Hero */
  .hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
  }
  .hero h1 {
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #E94560 0%, #F5A623 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .hero p {
    color: #A0A0B0;
    font-size: 1rem;
    margin-top: 0;
  }

  /* Card */
  .card {
    background: #1A1A2E;
    border: 1px solid #2A2A45;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
  }

  /* Pipeline bar */
  .pipeline {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin: 1.5rem 0;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
  }
  .pipe-step {
    background: #2A2A45;
    border-radius: 8px;
    padding: 0.4rem 0.9rem;
    color: #A0A0B0;
    transition: all 0.3s;
  }
  .pipe-step.active {
    background: #E94560;
    color: #fff;
    box-shadow: 0 0 12px rgba(233,69,96,0.5);
  }
  .pipe-step.done {
    background: #2A4535;
    color: #4CAF50;
    border: 1px solid #4CAF50;
  }
  .pipe-arrow { color: #3A3A5A; font-size: 1rem; }

  /* Inputs */
  .stTextInput > div > div > input,
  .stSelectbox > div > div,
  .stTextArea > div > div > textarea {
    background: #12122A !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 10px !important;
    color: #F5F5F5 !important;
    font-family: 'Inter', sans-serif !important;
  }

  /* Buttons */
  .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #E94560, #C0392B);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.75rem 1.5rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: opacity 0.2s;
    margin-top: 0.5rem;
  }
  .stButton > button:hover { opacity: 0.88; }

  /* Status tags */
  .tag {
    display: inline-block;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'Space Grotesk', sans-serif;
  }
  .tag-running { background: #2A3A5A; color: #5B9BD5; }
  .tag-done    { background: #2A4535; color: #4CAF50; }
  .tag-error   { background: #3A2020; color: #E94560; }

  /* Output box */
  .output-box {
    background: #101025;
    border: 1px solid #2A2A45;
    border-radius: 12px;
    padding: 1.5rem;
    white-space: pre-wrap;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #E0E0F0;
    max-height: 500px;
    overflow-y: auto;
  }

  /* Log box */
  .log-box {
    background: #080816;
    border: 1px solid #1A1A3A;
    border-radius: 10px;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #6A9FBF;
    max-height: 250px;
    overflow-y: auto;
    line-height: 1.5;
  }

  /* Section labels */
  .section-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #A0A0B0;
    margin-bottom: 0.4rem;
  }

  .divider {
    border: none;
    border-top: 1px solid #1E1E3A;
    margin: 1.5rem 0;
  }
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>YouTube → Blog Generator</h1>
  <p>Powered by CrewAI &nbsp;·&nbsp; Groq LLM &nbsp;·&nbsp; Two AI Agents</p>
</div>
""", unsafe_allow_html=True)

# ── Pipeline visualization ────────────────────────────────────────────────────
def pipeline_html(stage: str):
    """stage: 'idle' | 'research' | 'write' | 'done'"""
    steps = {
        "Research Agent": "research",
        "Writer Agent": "write",
        "Blog Ready": "done_step",
    }
    html = '<div class="pipeline">'
    for label, key in steps.items():
        css = "pipe-step"
        if stage == key:
            css += " active"
        elif (stage == "write" and key == "research") or (stage == "done_step" and key in ("research", "write")):
            css += " done"
        html += f'<div class="{css}">{label}</div>'
        if key != "done_step":
            html += '<span class="pipe-arrow">→</span>'
    html += "</div>"
    return html

pipeline_placeholder = st.empty()
pipeline_placeholder.markdown(pipeline_html("idle"), unsafe_allow_html=True)

# ── Input card ───────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown('<div class="section-label">YouTube Channel</div>', unsafe_allow_html=True)
channel_handle = st.text_input(
    label="channel",
    value="@krishnaik06",
    placeholder="e.g. @krishnaik06 or full channel URL",
    label_visibility="collapsed",
)

st.markdown('<div class="section-label">Topic / Video Title</div>', unsafe_allow_html=True)
topic = st.text_input(
    label="topic",
    value="",
    placeholder="e.g. AI VS ML VS DL vs Data Science",
    label_visibility="collapsed",
)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="section-label">Groq Model</div>', unsafe_allow_html=True)
    groq_model = st.selectbox(
        label="model",
        options=[
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        ],
        label_visibility="collapsed",
    )
with col2:
    st.markdown('<div class="section-label">Output File</div>', unsafe_allow_html=True)
    output_file = st.text_input(
        label="output",
        value="new-blog-post.md",
        label_visibility="collapsed",
    )

# API key check
groq_key = os.getenv("GROQ_API_KEY", "")
if not groq_key:
    st.warning("⚠️  `GROQ_API_KEY` not found in environment. Add it to your `.env` file.")

run_btn = st.button("🚀  Generate Blog Post")
st.markdown("</div>", unsafe_allow_html=True)

# ── Run logic ─────────────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.error("Please enter a topic before running.")
        st.stop()
    if not channel_handle.strip():
        st.error("Please enter a YouTube channel handle.")
        st.stop()

    status_placeholder  = st.empty()
    log_placeholder     = st.empty()
    result_placeholder  = st.empty()

    # Show research stage
    pipeline_placeholder.markdown(pipeline_html("research"), unsafe_allow_html=True)
    status_placeholder.markdown('<span class="tag tag-running">⏳ Researcher agent working…</span>', unsafe_allow_html=True)

    log_lines = []

    # Capture stdout for live logs
    class StreamCapture:
        def __init__(self, original):
            self._original = original
            self.lines = []
        def write(self, text):
            self._original.write(text)
            if text.strip():
                self.lines.append(text.rstrip())
        def flush(self):
            self._original.flush()

    capture = StreamCapture(sys.stdout)
    sys.stdout = capture

    result_text = None
    error_text  = None

    try:
        from crew import run_crew

        # Patch: update pipeline mid-run isn't trivially possible in synchronous
        # Streamlit — we run the whole crew then update UI after.
        result_text = run_crew(
            topic=topic.strip(),
            youtube_channel_handle=channel_handle.strip(),
            groq_model=groq_model,
            output_file=output_file.strip(),
        )
    except Exception as e:
        error_text = str(e)
    finally:
        sys.stdout = capture._original

    # ── Results ──────────────────────────────────────────────────────────────
    if error_text:
        pipeline_placeholder.markdown(pipeline_html("idle"), unsafe_allow_html=True)
        status_placeholder.markdown(f'<span class="tag tag-error">❌ Error</span>', unsafe_allow_html=True)
        st.error(f"**Something went wrong:**\n\n```\n{error_text}\n```")

        if capture.lines:
            st.markdown("**Agent logs:**")
            st.markdown(
                f'<div class="log-box">' + "\n".join(capture.lines[-60:]) + "</div>",
                unsafe_allow_html=True,
            )
    else:
        pipeline_placeholder.markdown(pipeline_html("done_step"), unsafe_allow_html=True)
        status_placeholder.markdown('<span class="tag tag-done">✅ Blog generated!</span>', unsafe_allow_html=True)

        # Check if file was saved
        if Path(output_file.strip()).exists():
            with open(output_file.strip(), "r", encoding="utf-8") as f:
                file_content = f.read()
            st.download_button(
                label="⬇️  Download Blog Post (.md)",
                data=file_content,
                file_name=Path(output_file.strip()).name,
                mime="text/markdown",
            )

        # Display result
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Generated Blog Post</div>', unsafe_allow_html=True)
        result_str = str(result_text)
        st.markdown(f'<div class="output-box">{result_str}</div>', unsafe_allow_html=True)

        # Render as markdown below
        st.markdown("---")
        st.markdown("**Preview (rendered):**")
        st.markdown(result_str)

        # Agent logs collapsible
        if capture.lines:
            with st.expander("🔍 Agent logs"):
                st.markdown(
                    '<div class="log-box">' + "<br>".join(capture.lines) + "</div>",
                    unsafe_allow_html=True,
                )

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top:3rem; color:#3A3A5A; font-size:0.78rem; font-family:'Space Grotesk',sans-serif;">
  CrewAI · Groq · YoutubeChannelSearchTool
</div>
""", unsafe_allow_html=True)
