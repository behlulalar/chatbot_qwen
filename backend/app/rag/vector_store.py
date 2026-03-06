"""
Vector Store Manager - Manages ChromaDB vector store for RAG.
"""
from typing import List, Optional, Dict
from pathlib import Path

from pydantic import SecretStr
from langchain_core.documents import Document

try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    OllamaEmbeddings = None

from langchain_openai import OpenAIEmbeddings

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("vector_store", "./logs/vector_store.log")


class VectorStoreManager:
    """
    Manages ChromaDB vector store operations.
    
    Features:
    - Create/load vector store
    - Add documents with embeddings
    - Search similar documents
    - Manage collections
    
    Usage:
        manager = VectorStoreManager()
        manager.create_or_load()
        manager.add_documents(chunks)
        results = manager.search("query", k=5)
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "mevzuat_collection"
    ):
        """
        Initialize vector store manager.
        
        Args:
            persist_directory: Directory to persist ChromaDB
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        self.vectorstore = None
        self.embeddings = None
        
        # Create persist directory
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VectorStoreManager initialized: {self.persist_directory}")
    
    def initialize_embeddings(self, openai_api_key: Optional[str] = None):
        """
        Initialize embeddings — Ollama (local) or OpenAI (API) based on config.

        Uses Ollama when LLM_BASE_URL is set (local deployment).
        Falls back to OpenAI when no base_url is configured.
        """
        base_url = settings.llm_base_url

        if base_url and OllamaEmbeddings is not None:
            ollama_host = base_url.replace("/v1", "")
            self.embeddings = OllamaEmbeddings(
                model=settings.embedding_model,
                base_url=ollama_host,
            )
            logger.info(f"Ollama embeddings initialized: {settings.embedding_model} @ {ollama_host}")
        else:
            api_key = openai_api_key or settings.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key required for embeddings")
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=SecretStr(api_key),
            )
            logger.info(f"OpenAI embeddings initialized: {settings.embedding_model}")
    
    def create_or_load(self) -> Chroma:
        """
        Create new or load existing vector store.
        
        Returns:
            Chroma vector store instance
        """
        if not self.embeddings:
            self.initialize_embeddings()
        
        # Check if vector store already exists
        chroma_path = Path(self.persist_directory)
        exists = chroma_path.exists() and list(chroma_path.glob("*"))
        
        if exists:
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            logger.info(f"Creating new vector store at {self.persist_directory}")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        
        return self.vectorstore
    
    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to vector store in batches.
        
        Args:
            documents: List of Document objects to add
            batch_size: Number of documents to process at once
        
        Returns:
            List of document IDs
        """
        if not self.vectorstore:
            self.create_or_load()
        assert self.vectorstore is not None

        logger.info(f"Adding {len(documents)} documents to vector store (batch_size={batch_size})")
        
        all_ids = []
        
        # Process in batches to avoid memory issues
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            try:
                ids = self.vectorstore.add_documents(batch)
                all_ids.extend(ids)
                logger.debug(f"Batch {batch_num} added successfully")
            except Exception as e:
                logger.error(f"Error adding batch {batch_num}: {e}", exc_info=True)
                raise
        
        logger.info(f"Successfully added {len(all_ids)} documents to vector store")
        return all_ids
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters (e.g., {"title": "YÖNERGE"})
        
        Returns:
            List of similar Document objects
        """
        if not self.vectorstore:
            self.create_or_load()
        assert self.vectorstore is not None

        logger.debug(f"Searching for: '{query}' (k={k})")
        
        if filter_dict:
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vectorstore.similarity_search(query, k=k)
        
        logger.debug(f"Found {len(results)} results")
        return results
    
    def search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Search with relevance scores.
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Metadata filters
        
        Returns:
            List of (Document, score) tuples
        """
        if not self.vectorstore:
            self.create_or_load()
        assert self.vectorstore is not None

        logger.debug(f"Searching with scores: '{query}' (k={k})")
        
        if filter_dict:
            results = self.vectorstore.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        logger.debug(f"Found {len(results)} results with scores")
        return results
    
    def delete_collection(self):
        """Delete the entire collection."""
        if self.vectorstore:
            logger.warning(f"Deleting collection: {self.collection_name}")
            self.vectorstore.delete_collection()
            self.vectorstore = None
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        if not self.vectorstore:
            self.create_or_load()
        assert self.vectorstore is not None

        try:
            # Get collection
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "error": str(e)
            }
    
    def as_retriever(self, search_kwargs: Optional[Dict] = None):
        """
        Get retriever interface for LangChain.
        
        Args:
            search_kwargs: Search parameters (e.g., {"k": 5})
        
        Returns:
            LangChain retriever object
        """
        if not self.vectorstore:
            self.create_or_load()
        assert self.vectorstore is not None

        search_kwargs = search_kwargs or {"k": 5}
        
        retriever = self.vectorstore.as_retriever(
            search_kwargs=search_kwargs
        )
        
        logger.debug(f"Created retriever with kwargs: {search_kwargs}")
        return retriever
