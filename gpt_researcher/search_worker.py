import json
from typing import Any, Dict, List, Optional

from gpt_researcher.actions.retriever import get_retriever, get_default_retriever


def run_search(
    query: str,
    retriever_name: str = "tavily",
    max_results: int = 10,
    query_domains: Optional[List[str]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a web search using one of the project's retrievers and return normalized results.

    Args:
        query: Search query string
        retriever_name: Name of retriever to use (e.g., "tavily", "duckduckgo", "google", etc.)
        max_results: Maximum number of results to return
        query_domains: Optional list of domains to include in the search
        headers: Optional headers passed to retrievers that support it (e.g., Tavily API key)

    Returns:
        A list of result dicts, normalized per retriever implementation
    """
    retriever_cls = get_retriever(retriever_name) or get_default_retriever()

    init_kwargs: Dict[str, Any] = {"query": query, "query_domains": query_domains}

    # Some retrievers (e.g., Tavily) accept headers; others ignore unknown kwargs
    # We'll pass headers only if provided and only for retrievers that are known to support it.
    if headers and retriever_name.lower() in {"tavily"}:
        init_kwargs["headers"] = headers

    retriever = retriever_cls(**init_kwargs)
    results = retriever.search(max_results=max_results)
    return results


def _print_results(results: List[Dict[str, Any]]) -> None:
    try:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception:
        # Fallback in case of non-serializable objects
        print(json.dumps([dict(r) for r in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a web search using gpt-researcher retrievers.")
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument("--retriever", default="tavily", help="Retriever name (default: tavily)")
    parser.add_argument("--max_results", type=int, default=10, help="Max results to fetch (default: 10)")
    parser.add_argument(
        "--query_domains",
        nargs="*",
        default=None,
        help="Optional list of domains to include in the search",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Optional header in the form key=value (repeatable)",
    )

    args = parser.parse_args()

    headers: Dict[str, str] = {}
    for item in args.header or []:
        if "=" in item:
            key, value = item.split("=", 1)
            headers[key.strip()] = value.strip()

    results = run_search(
        query=args.query,
        retriever_name=args.retriever,
        max_results=args.max_results,
        query_domains=args.query_domains,
        headers=headers or None,
    )

    _print_results(results) 