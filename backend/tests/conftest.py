import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from rag_system import RAGSystem
from models import Course, Lesson, CourseChunk


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Config()
    config.anthropic_api_key = "test-key"
    config.chunk_size = 100
    config.chunk_overlap = 20
    config.max_results = 3
    config.vector_store_path = tempfile.mkdtemp()
    return config


@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    return Course(
        title="Test Course",
        instructor="Test Instructor",
        course_link="https://example.com/course",
        lessons=[
            Lesson(
                lesson_number=1,
                title="Introduction",
                lesson_link="https://example.com/lesson1"
            ),
            Lesson(
                lesson_number=2,
                title="Advanced Topics",
                lesson_link="https://example.com/lesson2"
            )
        ]
    )


@pytest.fixture
def sample_course_chunks():
    """Sample course chunks for testing"""
    return [
        CourseChunk(
            content="This is lesson 1 content about introduction to the topic.",
            course_title="Test Course",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="This is lesson 2 content about advanced concepts.",
            course_title="Test Course",
            lesson_number=2,
            chunk_index=0
        )
    ]


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    mock_store = Mock()
    mock_store.add_courses = Mock()
    mock_store.add_course_chunks = Mock()
    mock_store.search_content = Mock(return_value=[
        {
            'content': 'Test content',
            'course_title': 'Test Course',
            'lesson_number': 1,
            'distance': 0.1
        }
    ])
    mock_store.get_course_analytics = Mock(return_value={
        'total_courses': 1,
        'course_titles': ['Test Course']
    })
    mock_store.find_closest_course = Mock(return_value='Test Course')
    return mock_store


@pytest.fixture
def mock_ai_generator():
    """Mock AI generator for testing"""
    mock_ai = AsyncMock()
    mock_ai.generate_response = AsyncMock(return_value=(
        "This is a test response from the AI.",
        [{'text': 'Source 1', 'link': 'http://example.com'}]
    ))
    return mock_ai


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    mock_session = Mock()
    mock_session.create_session = Mock(return_value="test-session-123")
    mock_session.add_message = Mock()
    mock_session.get_conversation_history = Mock(return_value=[])
    return mock_session


@pytest.fixture
def mock_rag_system(mock_config, mock_vector_store, mock_ai_generator, mock_session_manager):
    """Mock RAG system with all dependencies mocked"""
    with patch('rag_system.VectorStore') as mock_vs_class, \
         patch('rag_system.AIGenerator') as mock_ai_class, \
         patch('rag_system.SessionManager') as mock_sm_class:
        
        mock_vs_class.return_value = mock_vector_store
        mock_ai_class.return_value = mock_ai_generator
        mock_sm_class.return_value = mock_session_manager
        
        rag = RAGSystem(mock_config)
        rag.vector_store = mock_vector_store
        rag.ai_generator = mock_ai_generator
        rag.session_manager = mock_session_manager
        
        # Mock the methods that will be called
        rag.query = AsyncMock()
        rag.get_course_analytics = Mock()
        
        return rag


@pytest.fixture
def test_app(mock_rag_system):
    """Create a test FastAPI app without static file mounting issues"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional
    
    app = FastAPI(title="Test Course Materials RAG System")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    class SourceItem(BaseModel):
        text: str
        link: Optional[str] = None

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[SourceItem]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            
            answer, sources = await mock_rag_system.query(request.query, session_id)
            
            source_items = []
            if sources:
                for src in sources:
                    if isinstance(src, dict):
                        source_items.append(SourceItem(text=src.get('text', ''), link=src.get('link')))
                    else:
                        source_items.append(SourceItem(text=str(src), link=None))
            
            return QueryResponse(
                answer=answer,
                sources=source_items,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System API"}
    
    return app


@pytest.fixture
def client(test_app):
    """Test client for FastAPI app"""
    return TestClient(test_app)


@pytest.fixture
def temp_docs_dir():
    """Temporary directory with sample documents"""
    temp_dir = tempfile.mkdtemp()
    
    course1_content = """Course Title: Introduction to Python
Course Link: https://example.com/python-course
Course Instructor: John Doe

Lesson 1: Getting Started
This is the introduction to Python programming.
Python is a versatile programming language.

Lesson 2: Variables and Data Types
Learn about different data types in Python.
Variables store data in memory."""
    
    with open(os.path.join(temp_dir, "course1.txt"), "w") as f:
        f.write(course1_content)
    
    yield temp_dir
    
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def cleanup_vector_store(mock_config):
    """Cleanup vector store directory after each test"""
    yield
    if os.path.exists(mock_config.vector_store_path):
        shutil.rmtree(mock_config.vector_store_path)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for AI generator tests"""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.content = [Mock()]
    mock_message.content[0].text = "Test AI response"
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    return mock_client