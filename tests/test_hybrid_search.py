"""Tests for the hybrid search router."""

import pytest
# from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routers.hybrid_search import router
from src.schemas.api.search import HybridSearchRequest, SearchResponse
from src.dependencies import get_opensearch_client, get_embeddings_service
from src.services.opensearch.factory import make_opensearch_client
from src.services.embeddings.factory import make_embeddings_service


# class MockOpenSearchClient:
#     """Mock OpenSearch client for testing."""
    
#     def __init__(self):
#         self.health_check_result = True
    
#     def health_check(self):
#         return self.health_check_result
    
#     def search_unified(self, query, query_embedding=None, size=10, from_=0, categories=None, latest=False, use_hybrid=True, min_score=0.0):
#         """Mock search results."""
#         return {
#             "total": 2,
#             "hits": [
#                 {
#                     "arxiv_id": "1234.56789",
#                     "title": "Test Paper 1",
#                     "authors": "John Doe",
#                     "abstract": "Abstract for test paper 1 about machine learning",
#                     "published_date": "2024-01-01",
#                     "pdf_url": "https://arxiv.org/pdf/1234.56789.pdf",
#                     "score": 0.95,
#                     "highlights": {"title": ["Test Paper"]},
#                     "chunk_text": "Sample chunk text from paper 1",
#                     "chunk_id": "chunk_1",
#                     "section_name": "Introduction"
#                 },
#                 {
#                     "arxiv_id": "9876.54321",
#                     "title": "Test Paper 2",
#                     "authors": "Jane Smith",
#                     "abstract": "Abstract for test paper 2 about neural networks",
#                     "published_date": "2024-02-01",
#                     "pdf_url": "https://arxiv.org/pdf/9876.54321.pdf",
#                     "score": 0.85,
#                     "highlights": {"abstract": ["neural networks"]},
#                     "chunk_text": "Sample chunk text from paper 2",
#                     "chunk_id": "chunk_2",
#                     "section_name": "Conclusion"
#                 }
#             ]
#         }


# class MockEmbeddingsService:
#     """Mock embeddings service for testing."""
    
#     async def embed_query(self, query):
#         """Return a mock embedding vector."""
#         return [0.1] * 768  # Mock 768-dimensional embedding


@pytest.fixture
def test_app():
    """Create a test FastAPI app with REAL dependencies (OpenSearch + Embeddings)."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    
    # Override with REAL services - must be callable (factory functions)
    app.dependency_overrides[get_opensearch_client] = lambda: make_opensearch_client()
    app.dependency_overrides[get_embeddings_service] = lambda: make_embeddings_service()
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_app)


class TestHybridSearch:
    """Test cases for hybrid search endpoint."""

    def test_hybrid_search_basic(self, client):
        """Test basic hybrid search functionality.
        
        Breakpoint location: src/routers/hybrid_search.py:13
        """
        # Set breakpoint at line 26 where embedding is generated
        response = client.post(
            "/api/v1/hybrid-search/",
            json={
                "query": "machine learning",
                "size": 5,
                "use_hybrid": True
            }
        )
        print(f"Response status: {response.status_code}")
        data = response.json()
        print(f"Response content: {data}")
        
        assert response.status_code == 200
        # assert data["query"] == "machine learning"
        # assert data["total"] == 2
        # assert len(data["hits"]) == 2
        # assert data["search_mode"] == "hybrid"

    def test_hybrid_search_bm25_only(self, client):
        """Test BM25-only search when use_hybrid is False.
        
        Breakpoint location: src/routers/hybrid_search.py:32-43
        """
        response = client.post(
            "/api/v1/hybrid-search/",
            json={
                "query": "neural networks",
                "size": 10,
                "use_hybrid": False
            }
        )
        print(f"Response status: {response.status_code}")
        data = response.json()
        print(f"Response content: {data}")
        
        assert response.status_code == 200
        assert data["search_mode"] == "bm25"

    def test_hybrid_search_with_categories(self, client):
        """Test hybrid search with category filtering.
        
        Breakpoint location: src/routers/hybrid_search.py:34-43
        """
        response = client.post(
            "/api/v1/hybrid-search/",
            json={
                "query": "reinforcement learning",
                "size": 5,
                "categories": ["cs.AI", "cs.LG"],
                "use_hybrid": True
            }
        )
        print(f"Response status: {response.status_code}")
        data = response.json()
        print(f"Response content: {data}")
        
        assert response.status_code == 200
        assert data["total"] == 2

    def test_hybrid_search_empty_query(self, client):
        """Test validation error for empty query.
        
        Breakpoint location: FastAPI validation layer
        """
        response = client.post(
            "/api/v1/hybrid-search/",
            json={
                "query": "",
                "size": 5,
                "use_hybrid": True
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.json()}")
        
        assert response.status_code == 422  # Validation error

    def test_hybrid_search_invalid_size(self, client):
        """Test validation error for invalid size parameter."""
        response = client.post(
            "/api/v1/hybrid-search/",
            json={
                "query": "test query",
                "size": 150,  # Exceeds max limit of 100
                "use_hybrid": True
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.json()}")
        
        assert response.status_code == 422  # Validation error

    def test_service_unavailable(self, test_app, client):
        """Test 503 error when search service is unavailable.
        
        Breakpoint location: src/routers/hybrid_search.py:20-21
        """
        # Override health check to return False
        # from src.dependencies import get_opensearch_client
        
        # mock_client = MockOpenSearchClient()
        # mock_client.health_check_result = False
        
        # def override_unavailable():
        #     return mock_client
        
        test_app.dependency_overrides[get_opensearch_client] = lambda: make_opensearch_client()
        
        response = client.post(
            "/api/v1/hybrid-search/",
            json={
                "query": "test query",
                "size": 5,
                "use_hybrid": True
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.json()}")
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()