"""
agents.py
---------
Builds the researcher and writer CrewAI agents backed by Groq.
No OpenAI dependency — uses YoutubeChannelTranscriptTool from tools.py.
"""

from crewai import Agent, LLM

import os
import litellm
from dotenv import load_dotenv

from tools import YoutubeChannelTranscriptTool

load_dotenv()

# Works both locally (.env) and on Streamlit Cloud (st.secrets)
try:
    import streamlit as st
    _groq_key = st.secrets["GROQ_API_KEY"]
except Exception:
    _groq_key = os.getenv("GROQ_API_KEY", "")

os.environ["GROQ_API_KEY"] = _groq_key
litellm.groq_key = _groq_key


def get_groq_llm(model: str = "llama-3.3-70b-versatile") -> LLM:
    """Returns a CrewAI LLM instance backed by Groq."""
    return LLM(
        model=f"groq/{model}",
        api_key=_groq_key,
        tool_choice="auto",
    )


def build_agents(yt_tool: YoutubeChannelTranscriptTool, groq_model: str = "llama-3.3-70b-versatile"):
    """
    Builds and returns the researcher and writer agents configured with Groq.
    """
    llm = get_groq_llm(groq_model)

    blog_researcher = Agent(
        role="Blog Researcher from Youtube Videos",
        goal="Get the relevant video transcription for the topic {topic} from the provided YouTube channel",
        verbose=True,
        memory=False,
        backstory=(
            "Expert in understanding videos in AI, Data Science, Machine Learning, "
            "and Generative AI — providing insightful summaries and analysis."
        ),
        tools=[yt_tool],
        llm=llm,
        allow_delegation=False,
    )

    blog_writer = Agent(
        role="Blog Writer",
        goal="Narrate compelling tech stories about the video {topic} from YouTube",
        verbose=True,
        memory=False,
        backstory=(
            "With a flair for simplifying complex topics, you craft engaging narratives "
            "that captivate and educate, bringing new discoveries to light in an accessible manner."
        ),
        tools=[yt_tool],
        llm=llm,
        allow_delegation=False,
    )

    return blog_researcher, blog_writer
