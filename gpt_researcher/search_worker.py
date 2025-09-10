import json
import asyncio
import time
from typing import Any, Dict, List, Optional

from gpt_researcher.actions.retriever import get_retriever, get_default_retriever
from gpt_researcher.scraper import Scraper
from gpt_researcher.utils.workers import WorkerPool

async def _scrape_and_map(urls: List[str], scraper: str, max_workers: int) -> Dict[str, str]:
    # 选择一个通用 UA，避免部分站点拒绝
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    s = Scraper(urls, user_agent=user_agent, scraper=scraper, worker_pool=WorkerPool(max_workers))
    results = await s.run()
    return {item["url"]: (item.get("raw_content") or "") for item in results}

def _expand_bodies(
    results: List[Dict[str, Any]],
    scraper: str = "bs",
    max_workers: int = 4,
    max_body_chars: int = 2000,
) -> List[Dict[str, Any]]:
    urls = [r.get("href") for r in results if r.get("href")]
    if not urls:
        return results
    content_map = asyncio.run(_scrape_and_map(urls, scraper=scraper, max_workers=max_workers))
    for r in results:
        u = r.get("href")
        if u in content_map and content_map[u]:
            # print("Expanded body for {0}".format(u))
            r["body"] = content_map[u][:max_body_chars]
    return results

def run_search(
    query: str,
    retriever_name: str = "google",
    max_results: int = 10,
    query_domains: Optional[List[str]] = None,
    headers: Optional[Dict[str, str]] = None,
    expand: bool = True,
    scraper: str = "bs",
    max_body_chars: int = 2000,
    max_workers: int = 4,
    max_retry: int = 3,
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

    max_retry = 3
    results = None
    while max_retry > 0:
        try:
            results = retriever.search(max_results=max_results)
            break
        except Exception as e:
            max_retry -= 1
            if 'protocol' in str(e).lower():
                print(f"Error: {e}")
                print('【网络技术性问题】先 sleep 60s 再重试')
                time.sleep(60)
            else:
                print(f"Unexpected error: {e}")
                raise e
            
            if max_retry == 0:
                raise Exception(f"Failed to retrieve results after 3 retries. Last error: {e}")

    if expand and results:
        print("Expanding bodies...")
        results = _expand_bodies(results, scraper=scraper, max_workers=max_workers, max_body_chars=max_body_chars)
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
    parser.add_argument("--expand", action="store_true", help="Fetch each href and expand body with page content")
    parser.add_argument("--scraper", default="bs", choices=["bs","web_base_loader","browser","nodriver","tavily_extract","firecrawl","pdf","arxiv"], help="Scraper backend (default: bs)")
    parser.add_argument("--max_body_chars", type=int, default=2000, help="Max characters to keep in expanded body")
    parser.add_argument("--max_workers", type=int, default=4, help="Concurrent scraper workers")

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
        expand=args.expand,
        scraper=args.scraper,
        max_body_chars=args.max_body_chars,
        max_workers=args.max_workers,
    )

    _print_results(results) 