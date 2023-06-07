import os
import time

from loguru import logger

from server.models.base import SearchResponse, SearchRequest, SearchResult, SourceReadRequest, Source
from server.services.browse import scrape_results, scrape_text
from server.services.search import google_search

consumer_api_key = os.environ.get("TWITTER_APP_KEY")
consumer_secret = os.environ.get("TWITTER_APP_SECRET")


async def duckduckgo_search(
        request: SearchRequest
) -> SearchResponse:
    logger.info(f'Request: {request}')
    start = time.time()
    # request = request.copy(update={'sources': 1, 'source_tokens': max(request.source_tokens, 1000)})
    results = google_search(request.query, num_results=request.sources)
    logger.debug(f'Search took {time.time() - start} seconds')
    results = await scrape_results(results)

    def trim_result(r: SearchResult) -> SearchResult:
        words = r.text.split()[:request.source_max_words]
        text = ' '.join(words)
        return r.copy(update={'text': text})

    results = [trim_result(r) for r in results]
    logger.debug(f'returning {len(results)} after {time.time() - start} seconds')
    return SearchResponse(__root__=results)


async def read_source_api(request: SourceReadRequest) -> Source:
    start = time.time()
    source = Source(link=request.link)
    result = await scrape_text(source)
    logger.debug(f'source read took {time.time() - start} seconds')
    words = result.text.split()[:request.max_words]
    text = ' '.join(words)
    return source.copy(update={'text': text})
