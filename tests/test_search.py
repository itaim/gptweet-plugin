import asyncio
import pprint

from dotenv import load_dotenv
from loguru import logger

from server import google_official_search, get_text_summary

load_dotenv()


def test_google_official_search():
    links = google_official_search('What is the situation with Trump indictments?', 3)
    assert len(links) == 3


def test_search_and_browse():
    question = 'What is the situation with the Trump indictments?'
    links = google_official_search(question, 3)
    answer = get_text_summary(links[1], question=question)
    logger.info('')
    logger.info(question)
    logger.info(answer)


def test_search_and_browse_multi():
    question = 'What is the situation with the Trump indictments?'
    links = google_official_search(question, 5)
    answers = asyncio.run(get_text_summary(links, question=question, return_results=3))
    logger.info(pprint.pformat(answers))
    assert len(answers) == 3
