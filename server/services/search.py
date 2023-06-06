import asyncio
import json
import os
from typing import List, Optional

from duckduckgo_search import ddg
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from server.models.base import SearchResult
from server.services.browse import scrape_text, scrape_links, summarize_text, TextSummary


def google_search(query, num_results=8) -> List[SearchResult]:
    try:
        ddg_results = ddg(query, max_results=num_results)
        return list(filter(lambda s: s.link, [
            SearchResult(link=ddg_dict.get('href', ''), title=ddg_dict.get('title', ''),
                         snippet=ddg_dict.get('body', ''))
            for ddg_dict in ddg_results]))
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        if error_details.get("error", {}).get("code") == 403 and "invalid API key" in error_details.get("error",
                                                                                                        {}).get(
            "message", ""):
            logger.error("Error: The provided Google API key is invalid or missing.")
        else:
            logger.error(f"Error: {e}")
        raise e


google_api_key = os.environ['GOOGLE_API_KEY']
custom_search_engine_id = os.environ['CUSTOM_SEARCH_ENGINE_ID']


def google_official_search(query, num_results=8) -> List[SearchResult]:
    try:
        service = build("customsearch", "v1", developerKey=google_api_key)
        result = service.cse().list(q=query, cx=custom_search_engine_id, num=num_results).execute()
        search_results = result.get("items", [])
        return list(filter(lambda s: s.link, [
            SearchResult(link=item.get('link', ''), title=item.get('title', ''),
                         snippet=item.get('snippet', ''))
            for item in search_results]))

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get("code") == 403 and "invalid API key" in error_details.get("error",
                                                                                                        {}).get(
            "message", ""):
            logger.error("Error: The provided Google API key is invalid or missing.")
        else:
            logger.error(f"Error: {e}")
        raise e


# async def browse_website(url, question):
#     summary = await get_text_summary(url, question)
#     links = get_hyperlinks(url)
#
#     # Limit links to 5
#     if len(links) > 5:
#         links = links[:5]
#
#     result = f"""Website Content Summary: {summary}\n\nLinks: {links}"""
#
#     return result
async def get_text_summaries(urls: List[str] | str, question: str, num_sources: int = 1, max_tokens: int = 500) -> \
        Optional[List[SearchResult]]:
    results = []
    if isinstance(urls, str):
        urls = [urls]

    async def summarize_source(url: str):
        text = scrape_text(url)
        if not text:
            return None
        logger.debug(f'Summarizing {url}')
        return await summarize_text(text=text, question=question, source=url, max_tokens=max_tokens)

    results = []

    async def add_summaries(start: int, end: int):
        tasks = [
            summarize_source(url) for url in urls[start:end]]
        gathered_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend([
            SearchResult(source=r.source, query=question, answer=r.summary) for r in gathered_results if
            isinstance(r, TextSummary)
        ])

    start_source_index = 0
    for end_source_index in range(min(len(urls), num_sources), len(urls) + 1):
        await add_summaries(start_source_index, end_source_index)
        if len(results) >= num_sources:
            break
        start_source_index = end_source_index

    if not results:
        return None
    else:
        return results


def get_hyperlinks(url):
    link_list = scrape_links(url)
    return link_list


async def get_search_results(query, return_results: int = 3, num_search: int = 8, max_tokens=600) -> Optional[
    List[SearchResult]]:
    links = google_official_search(query, num_search)
    return await get_text_summaries(links, question=query, num_sources=return_results, max_tokens=max_tokens)
