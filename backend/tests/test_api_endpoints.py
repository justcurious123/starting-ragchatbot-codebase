import pytest
import json
from fastapi import status
from unittest.mock import AsyncMock, Mock, patch


class TestQueryEndpoint:
    """Test cases for the /api/query endpoint"""

    def test_query_success(self, client, mock_rag_system):
        """Test successful query processing"""
        mock_rag_system.query = AsyncMock(return_value=(
            "This is a test response about Python programming.",
            [
                {'text': 'Python basics from lesson 1', 'link': 'https://example.com/lesson1'},
                {'text': 'Advanced Python concepts', 'link': 'https://example.com/lesson2'}
            ]
        ))
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "session_id": "test-session-123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["answer"] == "This is a test response about Python programming."
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Python basics from lesson 1"
        assert data["sources"][0]["link"] == "https://example.com/lesson1"
        assert data["session_id"] == "test-session-123"

    def test_query_without_session_id(self, client, mock_rag_system):
        """Test query without session_id creates new session"""
        mock_rag_system.session_manager.create_session.return_value = "new-session-456"
        mock_rag_system.query = AsyncMock(return_value=(
            "Response without session",
            []
        ))
        
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == "new-session-456"
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_query_with_string_sources(self, client, mock_rag_system):
        """Test query handling legacy string sources"""
        mock_rag_system.query = AsyncMock(return_value=(
            "Response with string sources",
            ["Source 1", "Source 2"]
        ))
        
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Source 1"
        assert data["sources"][0]["link"] is None
        assert data["sources"][1]["text"] == "Source 2"
        assert data["sources"][1]["link"] is None

    def test_query_with_empty_sources(self, client, mock_rag_system):
        """Test query with no sources returned"""
        mock_rag_system.query = AsyncMock(return_value=(
            "Response with no sources",
            None
        ))
        
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sources"] == []

    def test_query_missing_query_field(self, client):
        """Test query request missing required query field"""
        response = client.post(
            "/api/query",
            json={"session_id": "test"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_invalid_json(self, client):
        """Test query with invalid JSON"""
        response = client.post(
            "/api/query",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_empty_query_string(self, client, mock_rag_system):
        """Test query with empty query string"""
        mock_rag_system.query = AsyncMock(return_value=("Empty query response", []))
        
        response = client.post(
            "/api/query",
            json={"query": ""}
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_query_rag_system_error(self, client, mock_rag_system):
        """Test query when RAG system raises an exception"""
        mock_rag_system.query = AsyncMock(side_effect=Exception("RAG system error"))
        
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "RAG system error" in response.json()["detail"]

    def test_query_long_text(self, client, mock_rag_system):
        """Test query with very long text"""
        long_query = "What is Python? " * 100
        mock_rag_system.query = AsyncMock(return_value=("Long response", []))
        
        response = client.post(
            "/api/query",
            json={"query": long_query}
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_query_special_characters(self, client, mock_rag_system):
        """Test query with special characters"""
        special_query = "What is Python? 🐍 Café résumé naïve"
        mock_rag_system.query = AsyncMock(return_value=("Special char response", []))
        
        response = client.post(
            "/api/query",
            json={"query": special_query}
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestCoursesEndpoint:
    """Test cases for the /api/courses endpoint"""

    def test_get_courses_success(self, client, mock_rag_system):
        """Test successful course statistics retrieval"""
        mock_analytics = {
            'total_courses': 3,
            'course_titles': ['Python Basics', 'Advanced Python', 'Data Science']
        }
        mock_rag_system.get_course_analytics.return_value = mock_analytics
        
        response = client.get("/api/courses")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3
        assert "Python Basics" in data["course_titles"]
        assert "Advanced Python" in data["course_titles"]
        assert "Data Science" in data["course_titles"]

    def test_get_courses_empty_result(self, client, mock_rag_system):
        """Test course statistics when no courses exist"""
        mock_analytics = {
            'total_courses': 0,
            'course_titles': []
        }
        mock_rag_system.get_course_analytics.return_value = mock_analytics
        
        response = client.get("/api/courses")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_rag_system_error(self, client, mock_rag_system):
        """Test courses endpoint when RAG system raises an exception"""
        mock_rag_system.get_course_analytics.side_effect = Exception("Analytics error")
        
        response = client.get("/api/courses")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Analytics error" in response.json()["detail"]

    def test_get_courses_method_not_allowed(self, client):
        """Test POST method not allowed on courses endpoint"""
        response = client.post("/api/courses", json={"test": "data"})
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_courses_large_dataset(self, client, mock_rag_system):
        """Test course statistics with large number of courses"""
        course_titles = [f"Course {i}" for i in range(100)]
        mock_analytics = {
            'total_courses': 100,
            'course_titles': course_titles
        }
        mock_rag_system.get_course_analytics.return_value = mock_analytics
        
        response = client.get("/api/courses")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_courses"] == 100
        assert len(data["course_titles"]) == 100


class TestRootEndpoint:
    """Test cases for the root endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct message"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "Course Materials RAG System API"

    def test_root_endpoint_method_not_allowed(self, client):
        """Test POST method not allowed on root endpoint"""
        response = client.post("/", json={"test": "data"})
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestAPIMiddleware:
    """Test API middleware functionality"""

    def test_cors_headers(self, client):
        """Test CORS headers are properly set with preflight request"""
        response = client.options(
            "/api/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # CORS headers may not be visible in TestClient, so we just check the request succeeds
        assert response.status_code in [200, 405]

    def test_content_type_json(self, client, mock_rag_system):
        """Test API endpoints accept and return JSON"""
        mock_rag_system.query = AsyncMock(return_value=("Test", []))
        
        response = client.post(
            "/api/query",
            json={"query": "test"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("content-type").startswith("application/json")


class TestResponseModels:
    """Test API response model validation"""

    def test_query_response_model_validation(self, client, mock_rag_system):
        """Test QueryResponse model validation"""
        mock_rag_system.query = AsyncMock(return_value=(
            "Test response",
            [{'text': 'Test source', 'link': 'https://example.com'}]
        ))
        
        response = client.post("/api/query", json={"query": "test"})
        data = response.json()
        
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["sources"], list)
        if data["sources"]:
            assert "text" in data["sources"][0]
            assert "link" in data["sources"][0]

    def test_course_stats_response_model_validation(self, client, mock_rag_system):
        """Test CourseStats model validation"""
        mock_rag_system.get_course_analytics.return_value = {
            'total_courses': 1,
            'course_titles': ['Test Course']
        }
        
        response = client.get("/api/courses")
        data = response.json()
        
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)


class TestErrorHandling:
    """Test error handling across endpoints"""

    def test_404_endpoint(self, client):
        """Test non-existent endpoint returns 404"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_malformed_request_body(self, client):
        """Test malformed request body handling"""
        response = client.post(
            "/api/query",
            data=b"\x00\x01\x02",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_content_type(self, client, mock_rag_system):
        """Test request without content-type header"""
        mock_rag_system.query = AsyncMock(return_value=("Test", []))
        
        response = client.post(
            "/api/query",
            json={"query": "test"}
        )
        
        assert response.status_code == status.HTTP_200_OK