import os

from dotenv import load_dotenv
import pinecone
from loguru import logger
load_dotenv()

def test_pinecone():
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    assert api_key is not None
    assert environment is not None
    # Initialize Pinecone with the API key and environment
    pinecone.init(api_key=api_key, environment=environment)
    index = pinecone.Index('test')
    email_address = 'jones@rolebotics.com'
    res = index.upsert(vectors=[
        (
            email_address,  # Vector ID
            [0.0] * 1536,
            {"email": email_address},
        )])
    logger.info(res)
    res = index.query(id=email_address, top_k=10, include_metadata=True, include_values=True)
    logger.info(res)