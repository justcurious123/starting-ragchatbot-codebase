# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Quick start**: `./run.sh` (makes backend directory, starts uvicorn server on port 8000)
- **Manual start**: `cd backend && uv run uvicorn app:app --reload --port 8000`
- **Install dependencies**: `uv sync`

### Code Quality and Formatting
- **Format code**: `./format.sh` (runs black and isort formatting)
- **Check code quality**: `./lint.sh` (runs flake8, isort, and black checks)
- **Full quality pipeline**: `./quality.sh` (format + lint in sequence)
- **Manual commands**:
  - Format with black: `uv run black .`
  - Sort imports: `uv run isort .`
  - Lint with flake8: `uv run flake8 .`
  - Check formatting: `uv run black . --check --diff`
  - Check import order: `uv run isort . --check-only --diff`

### Environment Setup
- Create `.env` file with `ANTHROPIC_API_KEY=your-api-key-here` (see `.env.example`)
- The application loads documents from `../docs` folder on startup
- ChromaDB vector database persists in `./backend/chroma_db/`

## Architecture Overview

This is a **RAG (Retrieval-Augmented Generation) System** for querying course materials using semantic search and Anthropic's Claude API.

### Core Architecture Pattern
The system follows a **tool-based RAG pattern** where the AI uses function calling to search course content:

1. **User Query** → FastAPI endpoint (`/api/query`)
2. **RAG System** orchestrates all components
3. **AI Generator** uses Claude with **tool calling** to execute searches  
4. **Search Tool** performs semantic search via Vector Store
5. **Vector Store** searches ChromaDB collections
6. **Response** includes AI-generated answer + source citations

### Key Components

**RAGSystem** (`backend/rag_system.py`):
- Central orchestrator connecting all components
- Manages document ingestion from `../docs` folder
- Coordinates query processing with tool-based search

**VectorStore** (`backend/vector_store.py`):
- **Dual collection design**: 
  - `course_catalog`: Course metadata (titles, instructors, lessons)
  - `course_content`: Chunked course material for semantic search
- Uses sentence-transformers for embeddings (`all-MiniLM-L6-v2`)
- Smart course name resolution via semantic matching

**AIGenerator** (`backend/ai_generator.py`):
- Anthropic Claude integration with function calling
- System prompt optimized for educational content
- **Tool execution flow**: Claude → Search Tool → Follow-up Response

**DocumentProcessor** (`backend/document_processor.py`):
- Parses structured course documents with expected format:
  ```
  Course Title: [title]
  Course Link: [url] 
  Course Instructor: [instructor]
  Lesson X: [lesson title]
  [lesson content]
  ```
- Sentence-based chunking with configurable overlap (800 chars, 100 overlap)
- Creates CourseChunk objects with lesson context

**SearchTools** (`backend/search_tools.py`):
- Tool interface for Claude function calling
- CourseSearchTool supports course name filtering and lesson number filtering
- Tracks sources for UI display

### Data Models (`backend/models.py`)
- **Course**: Title, instructor, course_link, lessons[]
- **Lesson**: lesson_number, title, lesson_link  
- **CourseChunk**: content, course_title, lesson_number, chunk_index

### Configuration (`backend/config.py`)
- All settings centralized in dataclass
- Environment variable loading via python-dotenv
- Key settings: chunk_size=800, chunk_overlap=100, max_results=5

### API Endpoints (`backend/app.py`)
- `POST /api/query`: Main RAG query endpoint
- `GET /api/courses`: Course statistics and analytics
- Session management for conversation history
- Static file serving for frontend at root path

## Document Processing Flow

1. **Startup**: Loads all `.txt/.pdf/.docx` files from `../docs`
2. **Parsing**: Extracts course metadata and lesson structure
3. **Chunking**: Splits content into searchable chunks with lesson context
4. **Embedding**: Stores in ChromaDB with dual collection strategy
5. **Deduplication**: Avoids re-processing existing courses by title

## Search and Query Flow

1. **Query Processing**: User question sent to RAG system
2. **Tool Invocation**: Claude decides to use search_course_content tool
3. **Course Resolution**: If course name provided, semantic matching finds best match
4. **Content Search**: Vector search across course_content collection with filters
5. **Response Generation**: Claude synthesizes search results into educational response
6. **Source Tracking**: UI displays source citations from last search

## Key Design Decisions

- **Tool-based RAG**: Uses Claude's function calling instead of traditional retrieve-then-generate
- **Dual vector collections**: Separate course metadata from content for better search precision  
- **Session management**: Maintains conversation history with configurable limits
- **Smart chunking**: Sentence-based with lesson context injection for better retrieval
- **Code quality tools**: Black (formatting), isort (import sorting), flake8 (linting) configured for consistent code style
- **No testing framework**: This is a starting codebase without tests or CI/CD setup
- always use uv to run the server do not use pip directly
- use uv to run python files
- make sure to uv to manage all dependencies