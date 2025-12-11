import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from rag_system import RAGSystem
from models import Course, Lesson


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    config = Mock()
    config.CHUNK_SIZE = 200
    config.CHUNK_OVERLAP = 50
    config.CHROMA_PATH = "./test_chroma"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.MAX_RESULTS = 5
    config.ANTHROPIC_API_KEY = "test_key"
    config.ANTHROPIC_MODEL = "claude-test"
    config.MAX_HISTORY = 2
    return config


@pytest.fixture
def rag_system(mock_config):
    """Create a RAGSystem instance with mocked components"""
    with patch('rag_system.DocumentProcessor'), \
         patch('rag_system.VectorStore'), \
         patch('rag_system.AIGenerator'), \
         patch('rag_system.SessionManager'), \
         patch('rag_system.CourseSearchTool'), \
         patch('rag_system.CourseOutlineTool'):
        system = RAGSystem(mock_config)

        # Mock the components
        system.document_processor = Mock()
        system.vector_store = Mock()
        system.ai_generator = Mock()
        system.session_manager = Mock()
        system.tool_manager = Mock()
        system.search_tool = Mock()
        system.outline_tool = Mock()

        return system


@pytest.fixture
def sample_course_file(tmp_path):
    """Create a sample course file"""
    content = """Course Title: Test Course
Course Link: https://example.com
Course Instructor: Test Instructor

Lesson 0: Introduction
Lesson content here.
"""
    file_path = tmp_path / "test_course.txt"
    file_path.write_text(content)
    return str(file_path)


class TestRAGSystem:
    """Tests for RAGSystem class"""

    def test_init(self, mock_config):
        """Test RAGSystem initialization"""
        with patch('rag_system.DocumentProcessor') as mock_doc_proc, \
             patch('rag_system.VectorStore') as mock_vec_store, \
             patch('rag_system.AIGenerator') as mock_ai_gen, \
             patch('rag_system.SessionManager') as mock_session_mgr, \
             patch('rag_system.ToolManager') as mock_tool_mgr, \
             patch('rag_system.CourseSearchTool') as mock_search_tool, \
             patch('rag_system.CourseOutlineTool') as mock_outline_tool:

            system = RAGSystem(mock_config)

            # Verify all components were initialized
            mock_doc_proc.assert_called_once_with(200, 50)
            mock_vec_store.assert_called_once_with("./test_chroma", "all-MiniLM-L6-v2", 5)
            mock_ai_gen.assert_called_once_with("test_key", "claude-test")
            mock_session_mgr.assert_called_once_with(2)
            mock_tool_mgr.assert_called_once()

    def test_add_course_document_success(self, rag_system, sample_course_file):
        """Test successfully adding a course document"""
        # Mock document processor
        mock_course = Course(title="Test Course", lessons=[])
        mock_chunks = [Mock(), Mock()]
        rag_system.document_processor.process_course_document.return_value = (
            mock_course,
            mock_chunks
        )

        course, chunk_count = rag_system.add_course_document(sample_course_file)

        # Verify processing was called
        rag_system.document_processor.process_course_document.assert_called_once_with(
            sample_course_file
        )

        # Verify vector store was updated
        rag_system.vector_store.add_course_metadata.assert_called_once_with(mock_course)
        rag_system.vector_store.add_course_content.assert_called_once_with(mock_chunks)

        # Verify return values
        assert course == mock_course
        assert chunk_count == 2

    def test_add_course_document_error_handling(self, rag_system, sample_course_file):
        """Test error handling when adding course document"""
        # Mock an error
        rag_system.document_processor.process_course_document.side_effect = Exception("Test error")

        course, chunk_count = rag_system.add_course_document(sample_course_file)

        # Should return None and 0 on error
        assert course is None
        assert chunk_count == 0

    def test_add_course_folder_success(self, rag_system, tmp_path):
        """Test adding all courses from a folder"""
        # Create test files
        for i in range(3):
            file_path = tmp_path / f"course{i}.txt"
            file_path.write_text(f"Course content {i}")

        # Mock document processor
        def mock_process(file_path):
            return (
                Course(title=f"Course {file_path}", lessons=[]),
                [Mock(), Mock()]
            )

        rag_system.document_processor.process_course_document.side_effect = mock_process
        rag_system.vector_store.get_existing_course_titles.return_value = []

        total_courses, total_chunks = rag_system.add_course_folder(str(tmp_path))

        # Should process all 3 files
        assert rag_system.document_processor.process_course_document.call_count == 3
        assert total_courses == 3
        assert total_chunks == 6  # 2 chunks per course

    def test_add_course_folder_skip_existing(self, rag_system, tmp_path):
        """Test that existing courses are skipped"""
        # Create test files
        file1 = tmp_path / "course1.txt"
        file1.write_text("Course 1")
        file2 = tmp_path / "course2.txt"
        file2.write_text("Course 2")

        # Mock existing courses
        rag_system.vector_store.get_existing_course_titles.return_value = ["Course 1"]

        # Mock processing
        def mock_process(file_path):
            if "course1" in file_path:
                return Course(title="Course 1", lessons=[]), []
            else:
                return Course(title="Course 2", lessons=[]), [Mock()]

        rag_system.document_processor.process_course_document.side_effect = mock_process

        total_courses, total_chunks = rag_system.add_course_folder(str(tmp_path))

        # Only Course 2 should be added (Course 1 already exists)
        assert total_courses == 1
        assert total_chunks == 1

    def test_add_course_folder_clear_existing(self, rag_system, tmp_path):
        """Test clearing existing data before adding courses"""
        file1 = tmp_path / "course1.txt"
        file1.write_text("Course 1")

        rag_system.document_processor.process_course_document.return_value = (
            Course(title="Course 1", lessons=[]),
            [Mock()]
        )
        rag_system.vector_store.get_existing_course_titles.return_value = []

        rag_system.add_course_folder(str(tmp_path), clear_existing=True)

        # Verify clear was called
        rag_system.vector_store.clear_all_data.assert_called_once()

    def test_add_course_folder_nonexistent_path(self, rag_system):
        """Test handling of nonexistent folder path"""
        total_courses, total_chunks = rag_system.add_course_folder("/nonexistent/path")

        assert total_courses == 0
        assert total_chunks == 0

    def test_query_without_session(self, rag_system):
        """Test querying without a session"""
        # Mock AI response
        rag_system.ai_generator.generate_response.return_value = "Test answer"
        rag_system.tool_manager.get_last_sources.return_value = []
        rag_system.session_manager.get_conversation_history.return_value = None

        response, sources = rag_system.query("What is Python?")

        # Verify AI was called
        rag_system.ai_generator.generate_response.assert_called_once()
        call_args = rag_system.ai_generator.generate_response.call_args[1]

        assert "What is Python?" in call_args['query']
        assert call_args['conversation_history'] is None

        # Verify response
        assert response == "Test answer"
        assert sources == []

    def test_query_with_session(self, rag_system):
        """Test querying with a session for conversation context"""
        # Mock history
        rag_system.session_manager.get_conversation_history.return_value = (
            "User: Previous question\nAssistant: Previous answer"
        )
        rag_system.ai_generator.generate_response.return_value = "Test answer"
        rag_system.tool_manager.get_last_sources.return_value = []

        response, sources = rag_system.query("Follow-up question", session_id="session_1")

        # Verify history was retrieved
        rag_system.session_manager.get_conversation_history.assert_called_once_with("session_1")

        # Verify AI was called with history
        call_args = rag_system.ai_generator.generate_response.call_args[1]
        assert call_args['conversation_history'] is not None

        # Verify conversation was updated
        rag_system.session_manager.add_exchange.assert_called_once_with(
            "session_1",
            "Follow-up question",
            "Test answer"
        )

    def test_query_with_sources(self, rag_system):
        """Test that query returns sources from tools"""
        rag_system.ai_generator.generate_response.return_value = "Answer"
        rag_system.tool_manager.get_last_sources.return_value = [
            {"text": "Source 1", "link": "https://example.com"}
        ]
        rag_system.session_manager.get_conversation_history.return_value = None

        response, sources = rag_system.query("Question")

        assert len(sources) == 1
        assert sources[0]['text'] == "Source 1"

        # Verify sources were reset after retrieval
        rag_system.tool_manager.reset_sources.assert_called_once()

    def test_query_uses_tools(self, rag_system):
        """Test that query passes tools to AI generator"""
        rag_system.ai_generator.generate_response.return_value = "Answer"
        rag_system.tool_manager.get_tool_definitions.return_value = [
            {"name": "test_tool"}
        ]
        rag_system.tool_manager.get_last_sources.return_value = []
        rag_system.session_manager.get_conversation_history.return_value = None

        rag_system.query("Question")

        # Verify tools were passed
        call_args = rag_system.ai_generator.generate_response.call_args[1]
        assert call_args['tools'] == [{"name": "test_tool"}]
        assert call_args['tool_manager'] == rag_system.tool_manager

    def test_get_course_analytics(self, rag_system):
        """Test getting course analytics"""
        # Mock vector store
        rag_system.vector_store.get_course_count.return_value = 5
        rag_system.vector_store.get_existing_course_titles.return_value = [
            "Course 1", "Course 2", "Course 3", "Course 4", "Course 5"
        ]

        analytics = rag_system.get_course_analytics()

        assert analytics['total_courses'] == 5
        assert len(analytics['course_titles']) == 5
        assert "Course 1" in analytics['course_titles']

    def test_add_course_folder_filters_file_types(self, rag_system, tmp_path):
        """Test that only specific file types are processed"""
        # Create various file types
        (tmp_path / "course1.txt").write_text("Content")
        (tmp_path / "course2.pdf").write_text("Content")
        (tmp_path / "course3.docx").write_text("Content")
        (tmp_path / "readme.md").write_text("Content")  # Should be skipped
        (tmp_path / "data.json").write_text("Content")  # Should be skipped

        rag_system.document_processor.process_course_document.return_value = (
            Course(title="Course", lessons=[]),
            [Mock()]
        )
        rag_system.vector_store.get_existing_course_titles.return_value = []

        rag_system.add_course_folder(str(tmp_path))

        # Should only process .txt, .pdf, .docx files (3 total)
        assert rag_system.document_processor.process_course_document.call_count == 3

    def test_add_course_folder_handles_errors(self, rag_system, tmp_path):
        """Test that errors in processing individual files don't stop the process"""
        # Create test files
        (tmp_path / "course1.txt").write_text("Content 1")
        (tmp_path / "course2.txt").write_text("Content 2")
        (tmp_path / "course3.txt").write_text("Content 3")

        # Mock one file failing
        def mock_process(file_path):
            if "course2" in file_path:
                raise Exception("Processing error")
            return Course(title=f"Course {file_path}", lessons=[]), [Mock()]

        rag_system.document_processor.process_course_document.side_effect = mock_process
        rag_system.vector_store.get_existing_course_titles.return_value = []

        total_courses, total_chunks = rag_system.add_course_folder(str(tmp_path))

        # Should process 2 out of 3 files (one failed)
        assert total_courses == 2
        assert total_chunks == 2
