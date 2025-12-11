import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from session_manager import SessionManager, Message


class TestMessage:
    """Tests for the Message dataclass"""

    def test_message_creation(self):
        """Test creating a Message"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_fields(self):
        """Test Message has expected fields"""
        msg = Message(role="assistant", content="Hi there")
        assert hasattr(msg, "role")
        assert hasattr(msg, "content")


class TestSessionManager:
    """Tests for SessionManager class"""

    def test_init_default_max_history(self):
        """Test SessionManager initialization with default max_history"""
        manager = SessionManager()
        assert manager.max_history == 5
        assert manager.sessions == {}
        assert manager.session_counter == 0

    def test_init_custom_max_history(self):
        """Test SessionManager initialization with custom max_history"""
        manager = SessionManager(max_history=10)
        assert manager.max_history == 10

    def test_create_session(self):
        """Test creating a new session"""
        manager = SessionManager()
        session_id = manager.create_session()
        assert session_id == "session_1"
        assert session_id in manager.sessions
        assert manager.sessions[session_id] == []
        assert manager.session_counter == 1

    def test_create_multiple_sessions(self):
        """Test creating multiple sessions"""
        manager = SessionManager()
        session1 = manager.create_session()
        session2 = manager.create_session()
        session3 = manager.create_session()

        assert session1 == "session_1"
        assert session2 == "session_2"
        assert session3 == "session_3"
        assert manager.session_counter == 3

    def test_add_message_existing_session(self):
        """Test adding a message to an existing session"""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.add_message(session_id, "user", "Hello")

        assert len(manager.sessions[session_id]) == 1
        assert manager.sessions[session_id][0].role == "user"
        assert manager.sessions[session_id][0].content == "Hello"

    def test_add_message_new_session(self):
        """Test adding a message creates a new session if it doesn't exist"""
        manager = SessionManager()

        manager.add_message("new_session", "user", "Hello")

        assert "new_session" in manager.sessions
        assert len(manager.sessions["new_session"]) == 1

    def test_add_multiple_messages(self):
        """Test adding multiple messages to a session"""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.add_message(session_id, "user", "Hello")
        manager.add_message(session_id, "assistant", "Hi there")
        manager.add_message(session_id, "user", "How are you?")

        assert len(manager.sessions[session_id]) == 3
        assert manager.sessions[session_id][0].content == "Hello"
        assert manager.sessions[session_id][1].content == "Hi there"
        assert manager.sessions[session_id][2].content == "How are you?"

    def test_add_exchange(self):
        """Test adding a complete user-assistant exchange"""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.add_exchange(session_id, "What is Python?", "Python is a programming language")

        assert len(manager.sessions[session_id]) == 2
        assert manager.sessions[session_id][0].role == "user"
        assert manager.sessions[session_id][0].content == "What is Python?"
        assert manager.sessions[session_id][1].role == "assistant"
        assert manager.sessions[session_id][1].content == "Python is a programming language"

    def test_history_limit(self):
        """Test that conversation history is limited to max_history * 2"""
        manager = SessionManager(max_history=2)
        session_id = manager.create_session()

        # Add 3 exchanges (6 messages total)
        manager.add_exchange(session_id, "Q1", "A1")
        manager.add_exchange(session_id, "Q2", "A2")
        manager.add_exchange(session_id, "Q3", "A3")

        # Should only keep last 4 messages (2 exchanges)
        assert len(manager.sessions[session_id]) == 4
        assert manager.sessions[session_id][0].content == "Q2"
        assert manager.sessions[session_id][1].content == "A2"
        assert manager.sessions[session_id][2].content == "Q3"
        assert manager.sessions[session_id][3].content == "A3"

    def test_get_conversation_history_empty(self):
        """Test getting conversation history for empty session"""
        manager = SessionManager()
        session_id = manager.create_session()

        history = manager.get_conversation_history(session_id)

        assert history is None

    def test_get_conversation_history_nonexistent(self):
        """Test getting conversation history for nonexistent session"""
        manager = SessionManager()

        history = manager.get_conversation_history("nonexistent")

        assert history is None

    def test_get_conversation_history_none_session_id(self):
        """Test getting conversation history with None session_id"""
        manager = SessionManager()

        history = manager.get_conversation_history(None)

        assert history is None

    def test_get_conversation_history_formatted(self):
        """Test that conversation history is properly formatted"""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.add_exchange(session_id, "What is Python?", "Python is a programming language")
        manager.add_exchange(session_id, "Tell me more", "It's great for beginners")

        history = manager.get_conversation_history(session_id)

        expected = "User: What is Python?\nAssistant: Python is a programming language\nUser: Tell me more\nAssistant: It's great for beginners"
        assert history == expected

    def test_clear_session(self):
        """Test clearing all messages from a session"""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.add_exchange(session_id, "Hello", "Hi")
        assert len(manager.sessions[session_id]) == 2

        manager.clear_session(session_id)
        assert len(manager.sessions[session_id]) == 0

    def test_clear_nonexistent_session(self):
        """Test clearing a nonexistent session doesn't raise error"""
        manager = SessionManager()
        manager.clear_session("nonexistent")  # Should not raise error
