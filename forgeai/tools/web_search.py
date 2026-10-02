from typing import Annotated

from ddgs import DDGS
from langchain_core.tools import tool


@tool
def web_search(
    query: Annotated[str, "Search query to execute"],
    max_results: Annotated[int, "Maximum number of results to return"] = 5,
) -> str:
    """Search the web and return relevant results."""
    try:
        results = []

        with DDGS() as ddgs:
            search_results = ddgs.text(
                query,
                max_results=max_results,
            )

            for index, result in enumerate(search_results, start=1):
                title = result.get("title", "No Title")
                href = result.get("href", "No URL")
                body = result.get("body", "No Description")

                results.append(f"{index}. {title}\n" f"   URL: {href}\n" f"   {body}\n")

        if not results:
            return "No results found."

        return "\n".join(results)

    except Exception as error:
        return f"Error performing web search: {error!s}"


search_tools = [web_search]


__all__ = [
    "search_tools",
    "web_search",
]
