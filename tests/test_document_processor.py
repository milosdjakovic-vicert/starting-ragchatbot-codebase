import pytest
import sys
from pathlib import Path
import tempfile
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from document_processor import DocumentProcessor
from models import Course, CourseChunk


@pytest.fixture
def doc_processor():
    """Create a DocumentProcessor instance for testing"""
    return DocumentProcessor(chunk_size=200, chunk_overlap=50)


@pytest.fixture
def sample_course_file(tmp_path):
    """Create a sample course file for testing"""
    content = """Course Title: Introduction to Python
Course Link: https://example.com/python
Course Instructor: Jane Doe

Lesson 0: Getting Started
Lesson Link: https://example.com/python/lesson0
This is the introduction to Python programming. Python is a high-level programming language. It is great for beginners and experts alike.

Lesson 1: Variables and Data Types
Lesson Link: https://example.com/python/lesson1
Variables store data in Python. Common data types include integers, floats, strings, and booleans. You can use the type() function to check data types.
"""
    file_path = tmp_path / "python_course.txt"
    file_path.write_text(content)
    return str(file_path)


class TestDocumentProcessor:
    """Tests for DocumentProcessor class"""

    def test_init(self):
        """Test DocumentProcessor initialization"""
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 100

    def test_read_file(self, doc_processor, tmp_path):
        """Test reading a file with UTF-8 encoding"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        content = doc_processor.read_file(str(test_file))
        assert content == "Hello, World!"

    def test_read_file_with_unicode(self, doc_processor, tmp_path):
        """Test reading a file with unicode characters"""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text("Héllo Wörld 你好")

        content = doc_processor.read_file(str(test_file))
        assert "Héllo" in content
        assert "Wörld" in content
        assert "你好" in content

    def test_chunk_text_simple(self, doc_processor):
        """Test chunking simple text"""
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = doc_processor.chunk_text(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_text_respects_size(self):
        """Test that chunks respect the configured size"""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "This is a sentence. " * 20  # Long text with sentence breaks

        chunks = processor.chunk_text(text)

        # Most chunks should be near the chunk_size (allowing some flexibility)
        # At least one chunk should exist
        assert len(chunks) > 0
        # Chunks should be reasonable size (not all text in one chunk)
        assert len(chunks) > 1

    def test_chunk_text_with_overlap(self):
        """Test that chunks have proper overlap"""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = "This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence."

        chunks = processor.chunk_text(text)

        # With overlap, should have more chunks
        assert len(chunks) >= 2

    def test_chunk_text_empty_string(self, doc_processor):
        """Test chunking empty string"""
        chunks = doc_processor.chunk_text("")
        assert chunks == []

    def test_chunk_text_single_sentence(self, doc_processor):
        """Test chunking single sentence"""
        text = "This is a single sentence."
        chunks = doc_processor.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_process_course_document_basic(self, doc_processor, sample_course_file):
        """Test processing a basic course document"""
        course, chunks = doc_processor.process_course_document(sample_course_file)

        # Verify course metadata
        assert isinstance(course, Course)
        assert course.title == "Introduction to Python"
        assert course.course_link == "https://example.com/python"
        assert course.instructor == "Jane Doe"

        # Verify lessons
        assert len(course.lessons) == 2
        assert course.lessons[0].lesson_number == 0
        assert course.lessons[0].title == "Getting Started"
        assert course.lessons[0].lesson_link == "https://example.com/python/lesson0"

        assert course.lessons[1].lesson_number == 1
        assert course.lessons[1].title == "Variables and Data Types"

        # Verify chunks
        assert len(chunks) > 0
        assert all(isinstance(chunk, CourseChunk) for chunk in chunks)
        assert all(chunk.course_title == "Introduction to Python" for chunk in chunks)

    def test_process_course_document_chunks_have_content(self, doc_processor, sample_course_file):
        """Test that course chunks have proper content and metadata"""
        course, chunks = doc_processor.process_course_document(sample_course_file)

        # Check that chunks have content
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.course_title == course.title
            assert chunk.lesson_number is not None
            assert isinstance(chunk.chunk_index, int)

    def test_process_course_document_chunk_context(self, doc_processor, sample_course_file):
        """Test that chunks include lesson context"""
        course, chunks = doc_processor.process_course_document(sample_course_file)

        # At least some chunks should have lesson context
        context_found = False
        for chunk in chunks:
            if "Lesson" in chunk.content and "content:" in chunk.content:
                context_found = True
                break

        assert context_found

    def test_process_course_document_missing_metadata(self, doc_processor, tmp_path):
        """Test processing document with missing metadata"""
        content = """Some Title
Some content here without proper formatting.
This is lesson content.
"""
        file_path = tmp_path / "incomplete.txt"
        file_path.write_text(content)

        course, chunks = doc_processor.process_course_document(str(file_path))

        # Should still process, using fallbacks
        assert isinstance(course, Course)
        assert course.title is not None

    def test_process_course_document_no_lessons(self, doc_processor, tmp_path):
        """Test processing document with no lesson markers"""
        content = """Course Title: Test Course
Course Link: https://example.com
Course Instructor: Test Instructor

This is just some general content without lesson structure.
More content here.
"""
        file_path = tmp_path / "no_lessons.txt"
        file_path.write_text(content)

        course, chunks = doc_processor.process_course_document(str(file_path))

        assert isinstance(course, Course)
        assert course.title == "Test Course"
        # Should still create chunks from the content
        assert len(chunks) > 0

    def test_process_course_document_multiple_lessons(self, doc_processor, tmp_path):
        """Test processing document with multiple lessons"""
        content = """Course Title: Multi-Lesson Course
Course Link: https://example.com/course
Course Instructor: Instructor Name

Lesson 0: First Lesson
Lesson Link: https://example.com/lesson0
Content for first lesson.

Lesson 1: Second Lesson
Lesson Link: https://example.com/lesson1
Content for second lesson.

Lesson 2: Third Lesson
Lesson Link: https://example.com/lesson2
Content for third lesson.
"""
        file_path = tmp_path / "multi_lesson.txt"
        file_path.write_text(content)

        course, chunks = doc_processor.process_course_document(str(file_path))

        assert len(course.lessons) == 3
        assert course.lessons[0].lesson_number == 0
        assert course.lessons[1].lesson_number == 1
        assert course.lessons[2].lesson_number == 2

    def test_chunk_text_normalizes_whitespace(self, doc_processor):
        """Test that chunk_text normalizes whitespace"""
        text = "This   has    multiple     spaces.\n\n\nAnd multiple newlines."
        chunks = doc_processor.chunk_text(text)

        # Check that whitespace is normalized
        for chunk in chunks:
            assert "   " not in chunk  # No triple spaces
            assert "\n\n" not in chunk  # No double newlines

    def test_chunk_index_increments(self, doc_processor, sample_course_file):
        """Test that chunk indexes increment properly"""
        course, chunks = doc_processor.process_course_document(sample_course_file)

        # Check that chunk indexes are sequential
        indexes = [chunk.chunk_index for chunk in chunks]
        assert indexes == list(range(len(chunks)))

    def test_process_course_document_lesson_without_link(self, doc_processor, tmp_path):
        """Test processing lesson without a lesson link"""
        content = """Course Title: Test Course
Course Link: https://example.com
Course Instructor: Test Instructor

Lesson 0: Lesson Without Link
This lesson has no link specified.
Content goes here.
"""
        file_path = tmp_path / "no_link.txt"
        file_path.write_text(content)

        course, chunks = doc_processor.process_course_document(str(file_path))

        assert len(course.lessons) == 1
        assert course.lessons[0].lesson_link is None
