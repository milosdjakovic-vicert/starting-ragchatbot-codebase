import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import shutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from vector_store import VectorStore, SearchResults
from models import Course, Lesson


@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore for testing"""
    return Mock(spec=VectorStore)


@pytest.fixture
def course_search_tool(mock_vector_store):
    """Create a CourseSearchTool instance"""
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def course_outline_tool(mock_vector_store):
    """Create a CourseOutlineTool instance"""
    return CourseOutlineTool(mock_vector_store)


class TestCourseSearchTool:
    """Tests for CourseSearchTool class"""

    def test_init(self, course_search_tool, mock_vector_store):
        """Test CourseSearchTool initialization"""
        assert course_search_tool.store == mock_vector_store
        assert course_search_tool.last_sources == []

    def test_get_tool_definition(self, course_search_tool):
        """Test getting tool definition"""
        definition = course_search_tool.get_tool_definition()

        assert definition['name'] == 'search_course_content'
        assert 'description' in definition
        assert 'input_schema' in definition
        assert definition['input_schema']['type'] == 'object'
        assert 'query' in definition['input_schema']['properties']
        assert 'query' in definition['input_schema']['required']

    def test_execute_successful_search(self, course_search_tool, mock_vector_store):
        """Test successful search execution"""
        # Mock search results
        mock_results = SearchResults(
            documents=["Python is a programming language"],
            metadata=[{"course_title": "Python Course", "lesson_number": 1}],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

        result = course_search_tool.execute(query="Python")

        # Verify search was called
        mock_vector_store.search.assert_called_once_with(
            query="Python",
            course_name=None,
            lesson_number=None
        )

        # Verify result format
        assert isinstance(result, str)
        assert "Python Course" in result
        assert "Lesson 1" in result

    def test_execute_with_course_filter(self, course_search_tool, mock_vector_store):
        """Test search with course name filter"""
        mock_results = SearchResults(
            documents=["Content"],
            metadata=[{"course_title": "Python Course", "lesson_number": 1}],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = mock_results
        mock_vector_store.get_lesson_link.return_value = None

        course_search_tool.execute(query="Python", course_name="Python Course")

        mock_vector_store.search.assert_called_once_with(
            query="Python",
            course_name="Python Course",
            lesson_number=None
        )

    def test_execute_with_lesson_filter(self, course_search_tool, mock_vector_store):
        """Test search with lesson number filter"""
        mock_results = SearchResults(
            documents=["Content"],
            metadata=[{"course_title": "Python Course", "lesson_number": 1}],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = mock_results
        mock_vector_store.get_lesson_link.return_value = None

        course_search_tool.execute(query="Python", lesson_number=1)

        mock_vector_store.search.assert_called_once_with(
            query="Python",
            course_name=None,
            lesson_number=1
        )

    def test_execute_error_handling(self, course_search_tool, mock_vector_store):
        """Test handling of search errors"""
        mock_results = SearchResults.empty("Test error")
        mock_vector_store.search.return_value = mock_results

        result = course_search_tool.execute(query="Python")

        assert result == "Test error"

    def test_execute_empty_results(self, course_search_tool, mock_vector_store):
        """Test handling of empty search results"""
        mock_results = SearchResults(documents=[], metadata=[], distances=[])
        mock_vector_store.search.return_value = mock_results

        result = course_search_tool.execute(query="Python")

        assert "No relevant content found" in result

    def test_execute_empty_results_with_filters(self, course_search_tool, mock_vector_store):
        """Test empty results message includes filter information"""
        mock_results = SearchResults(documents=[], metadata=[], distances=[])
        mock_vector_store.search.return_value = mock_results

        result = course_search_tool.execute(
            query="Python",
            course_name="Test Course",
            lesson_number=1
        )

        assert "No relevant content found" in result
        assert "Test Course" in result
        assert "lesson 1" in result

    def test_format_results_tracks_sources(self, course_search_tool, mock_vector_store):
        """Test that format_results tracks sources"""
        mock_results = SearchResults(
            documents=["Content 1", "Content 2"],
            metadata=[
                {"course_title": "Course A", "lesson_number": 1},
                {"course_title": "Course B", "lesson_number": 2}
            ],
            distances=[0.1, 0.2]
        )
        mock_vector_store.get_lesson_link.side_effect = [
            "https://example.com/lesson1",
            "https://example.com/lesson2"
        ]

        course_search_tool._format_results(mock_results)

        # Verify sources were tracked
        assert len(course_search_tool.last_sources) == 2
        assert course_search_tool.last_sources[0]['text'] == "Course A - Lesson 1"
        assert course_search_tool.last_sources[0]['link'] == "https://example.com/lesson1"

    def test_format_results_without_lesson_number(self, course_search_tool, mock_vector_store):
        """Test formatting results without lesson numbers"""
        mock_results = SearchResults(
            documents=["Content"],
            metadata=[{"course_title": "Course A", "lesson_number": None}],
            distances=[0.1]
        )
        mock_vector_store.get_lesson_link.return_value = None

        result = course_search_tool._format_results(mock_results)

        assert "[Course A]" in result
        assert "Lesson" not in result


class TestCourseOutlineTool:
    """Tests for CourseOutlineTool class"""

    def test_init(self, course_outline_tool, mock_vector_store):
        """Test CourseOutlineTool initialization"""
        assert course_outline_tool.store == mock_vector_store
        assert course_outline_tool.last_sources == []

    def test_get_tool_definition(self, course_outline_tool):
        """Test getting tool definition"""
        definition = course_outline_tool.get_tool_definition()

        assert definition['name'] == 'get_course_outline'
        assert 'description' in definition
        assert 'input_schema' in definition
        assert 'course_name' in definition['input_schema']['properties']
        assert 'course_name' in definition['input_schema']['required']

    def test_execute_successful(self, course_outline_tool, mock_vector_store):
        """Test successful outline retrieval"""
        import json

        # Mock course resolution
        mock_vector_store._resolve_course_name.return_value = "Python Course"

        # Mock catalog get
        mock_catalog = Mock()
        mock_catalog.get.return_value = {
            'metadatas': [{
                'title': 'Python Course',
                'instructor': 'Jane Doe',
                'course_link': 'https://example.com',
                'lessons_json': json.dumps([
                    {'lesson_number': 0, 'lesson_title': 'Introduction', 'lesson_link': None},
                    {'lesson_number': 1, 'lesson_title': 'Basics', 'lesson_link': 'https://example.com/lesson1'}
                ])
            }]
        }
        mock_vector_store.course_catalog = mock_catalog

        result = course_outline_tool.execute(course_name="Python")

        assert "Python Course" in result
        assert "Jane Doe" in result
        assert "Introduction" in result
        assert "Basics" in result

    def test_execute_course_not_found(self, course_outline_tool, mock_vector_store):
        """Test outline retrieval for nonexistent course"""
        mock_vector_store._resolve_course_name.return_value = None

        result = course_outline_tool.execute(course_name="Nonexistent")

        assert "No course found" in result
        assert "Nonexistent" in result

    def test_execute_no_metadata(self, course_outline_tool, mock_vector_store):
        """Test handling of missing metadata"""
        mock_vector_store._resolve_course_name.return_value = "Python Course"

        mock_catalog = Mock()
        mock_catalog.get.return_value = {'metadatas': []}
        mock_vector_store.course_catalog = mock_catalog

        result = course_outline_tool.execute(course_name="Python")

        assert "unable to retrieve outline" in result

    def test_execute_tracks_sources(self, course_outline_tool, mock_vector_store):
        """Test that execute tracks sources"""
        import json

        mock_vector_store._resolve_course_name.return_value = "Python Course"

        mock_catalog = Mock()
        mock_catalog.get.return_value = {
            'metadatas': [{
                'title': 'Python Course',
                'instructor': 'Jane Doe',
                'course_link': 'https://example.com/course',
                'lessons_json': json.dumps([])
            }]
        }
        mock_vector_store.course_catalog = mock_catalog

        course_outline_tool.execute(course_name="Python")

        assert len(course_outline_tool.last_sources) == 1
        assert "Python Course" in course_outline_tool.last_sources[0]['text']
        assert course_outline_tool.last_sources[0]['link'] == 'https://example.com/course'


class TestToolManager:
    """Tests for ToolManager class"""

    def test_init(self):
        """Test ToolManager initialization"""
        manager = ToolManager()
        assert manager.tools == {}

    def test_register_tool(self, course_search_tool):
        """Test registering a tool"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)

        assert 'search_course_content' in manager.tools
        assert manager.tools['search_course_content'] == course_search_tool

    def test_register_multiple_tools(self, course_search_tool, course_outline_tool):
        """Test registering multiple tools"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        manager.register_tool(course_outline_tool)

        assert len(manager.tools) == 2
        assert 'search_course_content' in manager.tools
        assert 'get_course_outline' in manager.tools

    def test_register_tool_without_name(self):
        """Test that registering tool without name raises error"""
        manager = ToolManager()

        # Create a mock tool with no name
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {}

        with pytest.raises(ValueError, match="Tool must have a 'name'"):
            manager.register_tool(mock_tool)

    def test_get_tool_definitions(self, course_search_tool, course_outline_tool):
        """Test getting all tool definitions"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        manager.register_tool(course_outline_tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 2
        assert any(d['name'] == 'search_course_content' for d in definitions)
        assert any(d['name'] == 'get_course_outline' for d in definitions)

    def test_execute_tool(self, course_search_tool, mock_vector_store):
        """Test executing a registered tool"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)

        # Mock the search
        mock_results = SearchResults(
            documents=["Content"],
            metadata=[{"course_title": "Course", "lesson_number": 1}],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = mock_results
        mock_vector_store.get_lesson_link.return_value = None

        result = manager.execute_tool('search_course_content', query="Python")

        assert isinstance(result, str)

    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist"""
        manager = ToolManager()

        result = manager.execute_tool('nonexistent_tool', query="test")

        assert "not found" in result

    def test_get_last_sources(self, course_search_tool):
        """Test getting last sources from tools"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)

        # Set some sources
        course_search_tool.last_sources = [
            {"text": "Source 1", "link": "https://example.com"}
        ]

        sources = manager.get_last_sources()

        assert len(sources) == 1
        assert sources[0]['text'] == "Source 1"

    def test_get_last_sources_no_sources(self):
        """Test getting last sources when no tools have sources"""
        manager = ToolManager()
        sources = manager.get_last_sources()
        assert sources == []

    def test_reset_sources(self, course_search_tool, course_outline_tool):
        """Test resetting sources from all tools"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        manager.register_tool(course_outline_tool)

        # Set sources
        course_search_tool.last_sources = [{"text": "Source 1", "link": None}]
        course_outline_tool.last_sources = [{"text": "Source 2", "link": None}]

        # Reset
        manager.reset_sources()

        # Verify all sources are cleared
        assert course_search_tool.last_sources == []
        assert course_outline_tool.last_sources == []
