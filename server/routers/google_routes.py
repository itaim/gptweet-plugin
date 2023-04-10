import os

from server.models.base import SearchResponse, SearchRequest

consumer_api_key = os.environ.get("TWITTER_APP_KEY")
consumer_secret = os.environ.get("TWITTER_APP_SECRET")


async def google_search(
        request: SearchRequest
):
    from server.services.search import get_text_summaries, google_official_search
    urls = google_official_search(request.query)
    if urls:
        results = await get_text_summaries(urls=urls, question=request.query, num_sources=request.sources,
                                           max_tokens=request.source_tokens)
        return SearchResponse(__root__=results)
    else:
        return SearchResponse(__root__=[])
