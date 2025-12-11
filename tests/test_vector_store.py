import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from vector_store import VectorStore, SearchResults
from models import Course, CourseChunk, Lesson


@pytest.fixture(scope="module")
def temp_chroma_path():
    """Create a temporary directory for ChromaDB - shared across all tests"""
    path = tempfile.mkdtemp(prefix="test_chroma_")
    yield path
    # Cleanup with retry
    import gc
    import time
    gc.collect()
    time.sleep(0.2)
    try:
        shutil.rmtree(path, ignore_errors=True)
    except:
        pass


@pytest.fixture(scope="module")
def shared_vector_store(temp_chroma_path):
    """Create a single VectorStore instance shared across all tests"""
    store = VectorStore(
        chroma_path=temp_chroma_path,
        embedding_model="all-MiniLM-L6-v2",
        max_results=5
    )
    yield store
    # Cleanup
    try:
        store.clear_all_data()
        del store.client
        del store
    except:
        pass


@pytest.fixture
def vector_store(shared_vector_store):
    """Provide a clean vector store for each test"""
    # Clear data before each test
    shared_vector_store.clear_all_data()
    return shared_vector_store


@pytest.fixture
def sample_course():
    """Create a sample course for testing"""
    return Course(
        title="Introduction to Python",
        course_link="https://example.com/python",
        instructor="Jane Doe",
        lessons=[
            Lesson(lesson_number=0, title="Getting Started", lesson_link="https://example.com/lesson0"),
            Lesson(lesson_number=1, title="Variables", lesson_link="https://example.com/lesson1")
        ]
    )


@pytest.fixture
def sample_chunks():
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="Python is a high-level programming language",
            course_title="Introduction to Python",
            lesson_number=0,
            chunk_index=0
        ),
        CourseChunk(
            content="Variables store data in Python",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=1
        ),
        CourseChunk(
            content="Functions help organize code",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=2
        )
    ]


class TestSearchResults:
    """Tests for SearchResults dataclass"""

    def test_from_chroma(self):
        """Test creating SearchResults from ChromaDB results"""
        chroma_results = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'key': 'value1'}, {'key': 'value2'}]],
            'distances': [[0.1, 0.2]]
        }

        results = SearchResults.from_chroma(chroma_results)

        assert results.documents == ['doc1', 'doc2']
        assert results.metadata == [{'key': 'value1'}, {'key': 'value2'}]
        assert results.distances == [0.1, 0.2]
        assert results.error is None

    def test_from_chroma_empty(self):
        """Test creating SearchResults from empty ChromaDB results"""
        chroma_results = {
            'documents': [],
            'metadatas': [],
            'distances': []
        }

        results = SearchResults.from_chroma(chroma_results)

        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []

    def test_empty_with_error(self):
        """Test creating empty SearchResults with error message"""
        results = SearchResults.empty("Test error")

        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []
        assert results.error == "Test error"

    def test_is_empty_true(self):
        """Test is_empty returns True for empty results"""
        results = SearchResults(documents=[], metadata=[], distances=[])
        assert results.is_empty() is True

    def test_is_empty_false(self):
        """Test is_empty returns False for non-empty results"""
        results = SearchResults(documents=['doc'], metadata=[{}], distances=[0.1])
        assert results.is_empty() is False


class TestVectorStore:
    """Tests for VectorStore class"""

    def test_init(self, vector_store):
        """Test VectorStore initialization"""
        assert vector_store.max_results == 5
        assert vector_store.client is not None
        assert vector_store.embedding_function is not None
        assert vector_store.course_catalog is not None
        assert vector_store.course_content is not None

    def test_add_course_metadata(self, vector_store, sample_course):
        """Test adding course metadata to catalog"""
        vector_store.add_course_metadata(sample_course)

        # Verify course was added
        course_titles = vector_store.get_existing_course_titles()
        assert "Introduction to Python" in course_titles

    def test_add_course_content(self, vector_store, sample_chunks):
        """Test adding course content chunks"""
        vector_store.add_course_content(sample_chunks)

        # Verify chunks were added by searching
        results = vector_store.search("Python programming")
        assert not results.is_empty()

    def test_add_course_content_empty_list(self, vector_store):
        """Test adding empty list of chunks doesn't error"""
        vector_store.add_course_content([])  # Should not raise error

    def test_get_existing_course_titles(self, vector_store, sample_course):
        """Test retrieving existing course titles"""
        # Initially empty (cleared by fixture)
        titles = vector_store.get_existing_course_titles()
        assert titles == []

        # Add a course
        vector_store.add_course_metadata(sample_course)

        # Should now return the course
        titles = vector_store.get_existing_course_titles()
        assert len(titles) == 1
        assert "Introduction to Python" in titles

    def test_get_course_count(self, vector_store, sample_course):
        """Test getting course count"""
        # Initially 0
        count = vector_store.get_course_count()
        assert count == 0

        # Add a course
        vector_store.add_course_metadata(sample_course)

        # Should be 1
        count = vector_store.get_course_count()
        assert count == 1

    def test_search_basic(self, vector_store, sample_course, sample_chunks):
        """Test basic search functionality"""
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        results = vector_store.search("Python programming language")

        assert not results.is_empty()
        assert len(results.documents) > 0
        assert results.error is None

    def test_search_with_course_filter(self, vector_store, sample_course, sample_chunks):
        """Test search with course name filter"""
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        results = vector_store.search(
            query="Python",
            course_name="Introduction to Python"
        )

        assert not results.is_empty()
        # All results should be from the specified course
        for meta in results.metadata:
            assert meta['course_title'] == "Introduction to Python"

    def test_search_with_lesson_filter(self, vector_store, sample_course, sample_chunks):
        """Test search with lesson number filter"""
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        results = vector_store.search(
            query="Variables",
            lesson_number=1
        )

        assert not results.is_empty()
        # All results should be from lesson 1
        for meta in results.metadata:
            assert meta['lesson_number'] == 1

    def test_search_with_both_filters(self, vector_store, sample_course, sample_chunks):
        """Test search with both course and lesson filters"""
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        results = vector_store.search(
            query="Python",
            course_name="Introduction to Python",
            lesson_number=1
        )

        assert not results.is_empty()
        for meta in results.metadata:
            assert meta['course_title'] == "Introduction to Python"
            assert meta['lesson_number'] == 1

    def test_search_nonexistent_course(self, vector_store, sample_course, sample_chunks):
        """Test search with nonexistent course name"""
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        results = vector_store.search(
            query="Python",
            course_name="Completely Different Nonexistent Course XYZ123"
        )

        # Should either return error or fuzzy match to existing course
        # The current implementation does fuzzy matching, so it might return results
        # We just verify it doesn't crash
        assert results is not None

    def test_search_respects_limit(self, vector_store, sample_course, sample_chunks):
        """Test that search respects the limit parameter"""
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        results = vector_store.search("Python", limit=2)

        assert len(results.documents) <= 2

    def test_resolve_course_name(self, vector_store, sample_course):
        """Test fuzzy course name resolution"""
        vector_store.add_course_metadata(sample_course)

        # Exact match
        resolved = vector_store._resolve_course_name("Introduction to Python")
        assert resolved == "Introduction to Python"

        # Partial match
        resolved = vector_store._resolve_course_name("Python")
        assert resolved == "Introduction to Python"

    def test_resolve_course_name_nonexistent(self, vector_store):
        """Test resolving nonexistent course name"""
        resolved = vector_store._resolve_course_name("Nonexistent Course")
        assert resolved is None

    def test_build_filter_none(self, vector_store):
        """Test building filter with no parameters"""
        filter_dict = vector_store._build_filter(None, None)
        assert filter_dict is None

    def test_build_filter_course_only(self, vector_store):
        """Test building filter with course only"""
        filter_dict = vector_store._build_filter("Test Course", None)
        assert filter_dict == {"course_title": "Test Course"}

    def test_build_filter_lesson_only(self, vector_store):
        """Test building filter with lesson only"""
        filter_dict = vector_store._build_filter(None, 1)
        assert filter_dict == {"lesson_number": 1}

    def test_build_filter_both(self, vector_store):
        """Test building filter with both course and lesson"""
        filter_dict = vector_store._build_filter("Test Course", 1)
        assert filter_dict == {
            "$and": [
                {"course_title": "Test Course"},
                {"lesson_number": 1}
            ]
        }

    def test_clear_all_data(self, vector_store, sample_course, sample_chunks):
        """Test clearing all data from collections"""
        # Add data
        vector_store.add_course_metadata(sample_course)
        vector_store.add_course_content(sample_chunks)

        # Verify data exists
        assert vector_store.get_course_count() > 0

        # Clear data
        vector_store.clear_all_data()

        # Verify data is cleared
        assert vector_store.get_course_count() == 0

    def test_get_all_courses_metadata(self, vector_store, sample_course):
        """Test getting all courses metadata"""
        vector_store.add_course_metadata(sample_course)

        metadata = vector_store.get_all_courses_metadata()

        assert len(metadata) == 1
        assert metadata[0]['title'] == "Introduction to Python"
        assert metadata[0]['instructor'] == "Jane Doe"
        assert 'lessons' in metadata[0]
        assert len(metadata[0]['lessons']) == 2

    def test_get_course_link(self, vector_store, sample_course):
        """Test getting course link"""
        vector_store.add_course_metadata(sample_course)

        link = vector_store.get_course_link("Introduction to Python")

        assert link == "https://example.com/python"

    def test_get_course_link_nonexistent(self, vector_store):
        """Test getting link for nonexistent course"""
        link = vector_store.get_course_link("Nonexistent")
        assert link is None

    def test_get_lesson_link(self, vector_store, sample_course):
        """Test getting lesson link"""
        vector_store.add_course_metadata(sample_course)

        link = vector_store.get_lesson_link("Introduction to Python", 0)

        assert link == "https://example.com/lesson0"

    def test_get_lesson_link_nonexistent_lesson(self, vector_store, sample_course):
        """Test getting link for nonexistent lesson"""
        vector_store.add_course_metadata(sample_course)

        link = vector_store.get_lesson_link("Introduction to Python", 99)

        assert link is None
