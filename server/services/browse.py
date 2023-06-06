import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Optional, List

import requests
from bs4 import BeautifulSoup
from loguru import logger

from server.models.base import SearchResult, Source
from server.services.llm_utils import async_chat_completion, ChatRequest


async def scrape_text(source: Source,timeout:float=6.0) -> Source:
    try:
        logger.debug(f'getting {source.link}')
        start = time.time()
        response = requests.get(source.link,timeout=timeout)
        logger.debug(f'{source.link} returned after {time.time()-start} seconds')
        if response.status_code >= 400:
            logger.warning(f'response status: {response.status_code} = {response.text}')
            # exception = HTTPException(status_code=response.status_code, detail=response.text)
            return source.copy(update={'text': response.text})
        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return source.copy(update={'text': text})
    except Exception as e:
        text = f'Error: {e.__repr__()}'
        return source.copy(update={'text': text})


def extract_hyperlinks(soup):
    hyperlinks = []
    for link in soup.find_all('a', href=True):
        hyperlinks.append((link.text, link['href']))
    return hyperlinks


def format_hyperlinks(hyperlinks):
    formatted_links = []
    for link_text, link_url in hyperlinks:
        formatted_links.append(f"{link_text} ({link_url})")
    return formatted_links


def scrape_links(url):
    response = requests.get(url)

    # Check if the response contains an HTTP error
    if response.status_code >= 400:
        return "error"

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    hyperlinks = extract_hyperlinks(soup)

    return format_hyperlinks(hyperlinks)


def split_text(text, max_length=3000):
    paragraphs = text.split("\n")
    current_length = 0
    current_chunk = []

    for i, paragraph in enumerate(paragraphs):
        if current_length + len(paragraph) + 1 <= max_length:
            current_chunk.append(paragraph)
            current_length += len(paragraph) + 1
        else:
            yield "\n".join(current_chunk)
            current_chunk = [paragraph]
            current_length = len(paragraph) + 1

    if current_chunk:
        yield "\n".join(current_chunk)


def create_message(chunk, question):
    return {
        "role": "user",
        "content": f"\"\"\"{chunk}\"\"\" Using the above text, please answer the following question: \"{question}\" -- if the question cannot be answered using the text, please summarize the text."
    }


@dataclass
class TextSummary:
    source: str
    summary: str


# async def scrape_results(results: List[SearchResult], timeout: int = 6) -> List[SearchResult]:
#     res_map = {r.link: r for r in results}
#     tasks = [scrape_text(result) for result in results]
#     start = time.time()
#     finished, unfinished = await asyncio.wait(tasks, timeout=timeout, return_when=asyncio.ALL_COMPLETED)
#
#     logger.debug(f'scraping completed after {time.time() - start} seconds')
#     for res in finished:
#         result = res.result()
#         if not isinstance(result, BaseException):
#             res_map[result.link] = result
#     return list(res_map.values())

import asyncio
import time
from typing import List

async def scrape_results(results: List[SearchResult], timeout: int = 6) -> List[SearchResult]:
    res_map = {r.link: r for r in results}
    tasks = [asyncio.wait_for(scrape_text(result), timeout=timeout) for result in results]
    start = time.time()

    finished, unfinished = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    logger.debug(f'scraping completed after {time.time() - start} seconds')
    for res in finished:
        try:
            result = res.result()
            if not isinstance(result, BaseException):
                res_map[result.link] = result
        except asyncio.TimeoutError:
            logger.debug(f'Task timed out after {timeout} seconds')
    return list(res_map.values())

async def summarize_text(text, question, source: Optional[str] = None, max_tokens=500) -> Optional[TextSummary]:
    if not text:
        logger.warning('No text to summarize')
        return None

    text_length = len(text)
    logger.debug(f"Text length: {text_length} characters")

    chunks = list(split_text(text))
    tasks = [
        async_chat_completion(
            request=ChatRequest.from_messages(messages=[create_message(chunk, question)], max_tokens=1600, key=i))
        for i, chunk in enumerate(chunks)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    def filter_result(result) -> bool:
        if isinstance(result, BaseException):
            logger.error(result)
            return False
        if result.exception:
            logger.error(f'{result.exception}')
            return False
        return True

    summaries = list(map(lambda c: c.reply, sorted(filter(lambda r: filter_result(r), results), key=lambda c: c.key())))
    logger.info(f"Summarized {len(chunks)} chunks.")

    combined_summary = "\n".join(summaries)
    messages = [create_message(combined_summary, question)]
    final_summary = await async_chat_completion(ChatRequest.from_messages(messages=messages, max_tokens=max_tokens))
    if final_summary.reply:
        source = source or hashlib.md5(text).hexdigest()
        return TextSummary(source=source, summary=final_summary.reply)
    else:
        return None
