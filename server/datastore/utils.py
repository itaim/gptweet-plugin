from typing import Optional

import pinecone
from loguru import logger


def get_or_create_index(index_name: str, metadata_config: Optional[dict], index_type: str = 'approximated') -> pinecone.Index:
    if index_name and index_name not in pinecone.list_indexes():
        # Get all fields in the metadata object in a list

        # Create a new index with the specified name, dimension, and metadata configuration
        try:
            print(
                f"Creating index {index_name} with metadata config {metadata_config}"
            )
            pinecone.create_index(
                index_name,
                index_type=index_type,
                dimension=1536,  # dimensionality of OpenAI ada v2 embeddings
                metadata_config=metadata_config
            )
            index = pinecone.Index(index_name)
            logger.info(f"Index {index_name} with metadata_config {metadata_config} created successfully")
            return index
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            raise e
    elif index_name and index_name in pinecone.list_indexes():
        # Connect to an existing index with the specified name
        try:
            logger.info(f"Connecting to existing index {index_name}")
            index = pinecone.Index(index_name)
            logger.info(f"Connected to index {index_name} successfully")
            return index
        except Exception as e:
            logger.info(f"Error connecting to index {index_name}: {e}")
            raise e
