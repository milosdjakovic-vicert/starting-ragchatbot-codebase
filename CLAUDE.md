# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system that answers questions about course materials using semantic search and Claude AI. The system uses ChromaDB for vector storage, sentence transformers for embeddings, and provides a FastAPI backend with a simple web frontend.

## Common Commands

### Setup and Dependencies
```bash
# Install dependencies
uv sync

# Create .env file with required API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Running the Application
```bash
# Start the web server (recommended - uses port 8800)
./run.sh

# Or manually start the server
cd backend && uv run uvicorn app:app --reload --port 8800
```

The application serves at http://localhost:8800 (web interface) and http://localhost:8800/docs (API documentation).

## Architecture Overview

### Core RAG Pipeline Flow
The system orchestrates a multi-component RAG pipeline:

1. **Document Ingestion** (document_processor.py):
   - Parses course files with structured format: Course Title, Link, Instructor, then Lessons
   - Extracts Course and Lesson objects with metadata
   - Chunks lesson content into overlapping segments (configurable via config.py)
   - Each chunk includes contextual headers (e.g., "Course X Lesson Y content: ...")

2. **Vector Storage** (vector_store.py):
   - Two ChromaDB collections:
     - `course_catalog`: Stores course metadata (title, instructor, lessons) for fuzzy course name matching
     - `course_content`: Stores chunked lesson content with metadata (course_title, lesson_number, chunk_index)
   - Semantic search with optional filters (course name, lesson number)
   - Course name resolution via vector similarity (e.g., "MCP" matches "Introduction to MCP")

3. **AI Tool-Calling Architecture** (search_tools.py + ai_generator.py):
   - Claude AI decides when to search using the `search_course_content` tool
   - Tool definition includes schema for: query (required), course_name (optional), lesson_number (optional)
   - Tool execution returns formatted results: `[Course - Lesson N]\ncontent`
   - ToolManager handles tool registration, execution, and source tracking

4. **Query Processing** (rag_system.py):
   - Receives user query with optional session_id
   - Retrieves conversation history from SessionManager
   - AI generates response using tool-calling (search_course_content available)
   - Sources extracted from tool searches and returned to frontend
   - Updates conversation history after response

### Key Component Relationships

- **RAGSystem** (rag_system.py): Main orchestrator that initializes and coordinates all components
  - Owns: DocumentProcessor, VectorStore, AIGenerator, SessionManager, ToolManager
  - Exposes: `query()`, `add_course_folder()`, `get_course_analytics()`

- **VectorStore** (vector_store.py): Dual-collection design
  - `search()` method: Resolves course name → filters content → returns SearchResults
  - Helper methods: `_resolve_course_name()`, `_build_filter()`

- **AIGenerator** (ai_generator.py): Claude API wrapper with tool execution
  - System prompt emphasizes: brief answers, one search max, no meta-commentary
  - Handles tool-calling loop: initial response → tool execution → final response
  - Uses temperature=0, max_tokens=800

- **ToolManager** (search_tools.py): Generic tool registration system
  - Any class implementing Tool interface (get_tool_definition, execute) can be registered
  - Tracks last sources for frontend display via `last_sources` attribute

### Configuration

All settings in backend/config.py (loaded from .env):
- ANTHROPIC_API_KEY: Required for Claude API
- ANTHROPIC_MODEL: Currently "claude-sonnet-4-20250514"
- EMBEDDING_MODEL: "all-MiniLM-L6-v2" (sentence transformers)
- CHUNK_SIZE: 800 chars, CHUNK_OVERLAP: 100 chars
- MAX_RESULTS: 5 search results per query
- MAX_HISTORY: 2 conversation exchanges kept in memory
- CHROMA_PATH: "./chroma_db" (persistent vector store)

### Document Format

Course documents (in docs/ folder) must follow this structure:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [url]
[lesson content...]

Lesson 1: [lesson title]
Lesson Link: [url]
[lesson content...]
```

On startup, backend/app.py loads all documents from ../docs folder into the vector store (skips duplicates).

### API Endpoints

FastAPI app (backend/app.py) exposes:
- POST /api/query: Main query endpoint (QueryRequest → QueryResponse with answer, sources, session_id)
- GET /api/courses: Returns CourseStats (total_courses, course_titles)
- Static files: Serves frontend/ at root path

### Session Management

SessionManager (backend/session_manager.py):
- In-memory conversation history per session
- Stores last N exchanges (configured by MAX_HISTORY)
- Session IDs auto-generated if not provided
- History formatted as "User: ...\nAssistant: ..." for AI context

### Frontend

Simple HTML/CSS/JS interface (frontend/):
- index.html: Main interface
- script.js: Handles API calls, session management, markdown rendering
- style.css: Styling
- Served via FastAPI StaticFiles at root path

## Important Notes

- The vector store persists in ./chroma_db - delete this directory to rebuild from scratch
- Course documents are only loaded on startup if not already in the vector store
- Tool-calling is automatic: Claude decides when to search based on query type
- Sources are extracted from search tools after each query and displayed in the frontend
- Run.sh uses port 8800 instead of 8000 (as shown in README)
