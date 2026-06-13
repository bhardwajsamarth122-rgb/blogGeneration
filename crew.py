from crewai import Crew, Process
from tools import get_yt_tool
from agents import build_agents
from tasks import build_tasks
import litellm

# Groq does not support the cache_breakpoint parameter that newer CrewAI
# injects into messages. This monkey-patch strips it before every request.
_original_completion = litellm.completion

def _patched_completion(*args, **kwargs):
    messages = kwargs.get("messages", [])
    for msg in messages:
        if isinstance(msg, dict):
            msg.pop("cache_breakpoint", None)
            if isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict):
                        block.pop("cache_breakpoint", None)
    kwargs["messages"] = messages
    return _original_completion(*args, **kwargs)

litellm.completion = _patched_completion


def run_crew(
    topic: str,
    youtube_channel_handle: str,
    groq_model: str = "llama-3.3-70b-versatile",
    output_file: str = "new-blog-post.md",
) -> str:
    """
    Runs the full crewAI pipeline for a given topic and YouTube channel.

    Args:
        topic: The topic/title to research and write about.
        youtube_channel_handle: YouTube channel handle (e.g. '@krishnaik06').
        groq_model: The Groq model to use.
        output_file: Path where the generated blog post will be saved.

    Returns:
        The result string from the crew run.
    """
    yt_tool = get_yt_tool(youtube_channel_handle)
    blog_researcher, blog_writer = build_agents(yt_tool, groq_model)
    research_task, write_task = build_tasks(blog_researcher, blog_writer, yt_tool, output_file)

    crew = Crew(
        agents=[blog_researcher, blog_writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        memory=False,
        cache=False,
        max_rpm=100,
        share_crew=False,
    )

    result = crew.kickoff(inputs={"topic": topic})
    return result


# ── CLI entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube → Blog CrewAI pipeline")
    parser.add_argument("--topic", required=True, help="Topic to research")
    parser.add_argument(
        "--channel",
        default="@krishnaik06",
        help="YouTube channel handle (default: @krishnaik06)",
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        help="Groq model name",
    )
    parser.add_argument(
        "--output",
        default="new-blog-post.md",
        help="Output markdown file path",
    )
    args = parser.parse_args()

    print(f"\n🚀 Starting crew for topic: '{args.topic}' on channel: {args.channel}\n")
    result = run_crew(
        topic=args.topic,
        youtube_channel_handle=args.channel,
        groq_model=args.model,
        output_file=args.output,
    )
    print("\n✅ Done!\n")
    print(result)
