"""
tasks.py
--------
Builds the research and writing CrewAI tasks.
No OpenAI dependency — type-hinted against YoutubeChannelTranscriptTool.
"""

from crewai import Task, Agent
from tools import YoutubeChannelTranscriptTool


def build_tasks(
    blog_researcher: Agent,
    blog_writer: Agent,
    yt_tool: YoutubeChannelTranscriptTool,
    output_file: str = "new-blog-post.md",
):
    """
    Builds and returns the research and writing tasks.

    Args:
        blog_researcher: The researcher agent.
        blog_writer: The writer agent.
        yt_tool: The YouTube search + transcript tool.
        output_file: File path where the blog post will be saved.

    Returns:
        Tuple of (research_task, write_task)
    """
    research_task = Task(
        description=(
            "Identify the video on the topic: {topic}. "
            "Get detailed information about the video from the YouTube channel."
        ),
        expected_output=(
            "A comprehensive 3-paragraph report based on the {topic} from the YouTube video content."
        ),
        tools=[yt_tool],
        agent=blog_researcher,
    )

    write_task = Task(
        description=(
            "Using the research gathered, write a full blog post about the topic: {topic}. "
            "The blog should be engaging, well-structured, and accessible to a general tech audience."
        ),
        expected_output=(
            "A well-written blog post summarizing and expanding on the YouTube video content "
            "for the topic: {topic}. Include an intro, main body sections, and a conclusion."
        ),
        tools=[yt_tool],
        agent=blog_writer,
        async_execution=False,
        output_file=output_file,
    )

    return research_task, write_task
