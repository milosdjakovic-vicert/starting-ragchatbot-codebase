import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from ai_generator import AIGenerator


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    return Mock()


@pytest.fixture
def ai_generator(mock_anthropic_client):
    """Create an AIGenerator instance with mocked client"""
    with patch('ai_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
        generator = AIGenerator(api_key="test_key", model="claude-test")
        generator.client = mock_anthropic_client
        return generator


class TestAIGenerator:
    """Tests for AIGenerator class"""

    def test_init(self):
        """Test AIGenerator initialization"""
        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            generator = AIGenerator(api_key="test_key", model="claude-sonnet-test")

            mock_anthropic.assert_called_once_with(api_key="test_key")
            assert generator.model == "claude-sonnet-test"
            assert generator.base_params['model'] == "claude-sonnet-test"
            assert generator.base_params['temperature'] == 0
            assert generator.base_params['max_tokens'] == 800

    def test_system_prompt_exists(self):
        """Test that system prompt is defined"""
        assert hasattr(AIGenerator, 'SYSTEM_PROMPT')
        assert isinstance(AIGenerator.SYSTEM_PROMPT, str)
        assert len(AIGenerator.SYSTEM_PROMPT) > 0

    def test_generate_response_simple(self, ai_generator, mock_anthropic_client):
        """Test generating a simple response without tools"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response")]

        mock_anthropic_client.messages.create.return_value = mock_response

        result = ai_generator.generate_response(query="Test query")

        # Verify API was called
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args[1]

        assert call_args['model'] == "claude-test"
        assert call_args['messages'][0]['content'] == "Test query"
        assert result == "Test response"

    def test_generate_response_with_history(self, ai_generator, mock_anthropic_client):
        """Test generating response with conversation history"""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with history")]

        mock_anthropic_client.messages.create.return_value = mock_response

        history = "User: Previous question\nAssistant: Previous answer"
        result = ai_generator.generate_response(
            query="New query",
            conversation_history=history
        )

        # Verify history was included in system prompt
        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert "Previous conversation:" in call_args['system']
        assert history in call_args['system']

    def test_generate_response_with_tools(self, ai_generator, mock_anthropic_client):
        """Test generating response with tools available"""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with tools")]

        mock_anthropic_client.messages.create.return_value = mock_response

        tools = [{"name": "test_tool", "description": "Test tool"}]
        result = ai_generator.generate_response(
            query="Test query",
            tools=tools
        )

        # Verify tools were included
        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert 'tools' in call_args
        assert call_args['tools'] == tools
        assert call_args['tool_choice'] == {"type": "auto"}

    def test_generate_response_tool_use(self, ai_generator, mock_anthropic_client):
        """Test handling tool use in response"""
        # Mock initial response with tool use
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_tool"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "test"}

        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        initial_response.content = [mock_tool_block]

        # Mock final response after tool execution
        final_response = Mock()
        final_response.content = [Mock(text="Final response")]

        mock_anthropic_client.messages.create.side_effect = [
            initial_response,
            final_response
        ]

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        tools = [{"name": "search_tool"}]
        result = ai_generator.generate_response(
            query="Test query",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_tool",
            query="test"
        )

        # Verify final response was returned
        assert result == "Final response"

        # Verify two API calls were made
        assert mock_anthropic_client.messages.create.call_count == 2

    def test_handle_tool_execution(self, ai_generator, mock_anthropic_client):
        """Test _handle_tool_execution method"""
        # Mock tool use block
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "test_tool"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"param": "value"}

        initial_response = Mock()
        initial_response.content = [mock_tool_block]

        # Mock final response
        final_response = Mock()
        final_response.content = [Mock(text="Final result")]

        mock_anthropic_client.messages.create.return_value = final_response

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool output"

        base_params = {
            "messages": [{"role": "user", "content": "Test"}],
            "system": "System prompt"
        }

        result = ai_generator._handle_tool_execution(
            initial_response,
            base_params,
            mock_tool_manager
        )

        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "test_tool",
            param="value"
        )

        # Verify result
        assert result == "Final result"

    def test_handle_tool_execution_multiple_tools(self, ai_generator, mock_anthropic_client):
        """Test handling multiple tool calls"""
        # Mock multiple tool blocks
        tool_block1 = Mock()
        tool_block1.type = "tool_use"
        tool_block1.name = "tool1"
        tool_block1.id = "id1"
        tool_block1.input = {"param": "value1"}

        tool_block2 = Mock()
        tool_block2.type = "tool_use"
        tool_block2.name = "tool2"
        tool_block2.id = "id2"
        tool_block2.input = {"param": "value2"}

        initial_response = Mock()
        initial_response.content = [tool_block1, tool_block2]

        final_response = Mock()
        final_response.content = [Mock(text="Final")]

        mock_anthropic_client.messages.create.return_value = final_response

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

        base_params = {
            "messages": [{"role": "user", "content": "Test"}],
            "system": "System"
        }

        ai_generator._handle_tool_execution(
            initial_response,
            base_params,
            mock_tool_manager
        )

        # Verify both tools were executed
        assert mock_tool_manager.execute_tool.call_count == 2

    def test_handle_tool_execution_ignores_non_tool_blocks(self, ai_generator, mock_anthropic_client):
        """Test that non-tool blocks are ignored"""
        text_block = Mock()
        text_block.type = "text"

        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "test_tool"
        tool_block.id = "id"
        tool_block.input = {}

        initial_response = Mock()
        initial_response.content = [text_block, tool_block]

        final_response = Mock()
        final_response.content = [Mock(text="Final")]

        mock_anthropic_client.messages.create.return_value = final_response

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Result"

        base_params = {
            "messages": [{"role": "user", "content": "Test"}],
            "system": "System"
        }

        ai_generator._handle_tool_execution(
            initial_response,
            base_params,
            mock_tool_manager
        )

        # Only the tool_use block should be executed
        assert mock_tool_manager.execute_tool.call_count == 1

    def test_base_params_configured_correctly(self, ai_generator):
        """Test that base_params are configured correctly"""
        assert ai_generator.base_params['model'] == "claude-test"
        assert ai_generator.base_params['temperature'] == 0
        assert ai_generator.base_params['max_tokens'] == 800

    def test_generate_response_without_history(self, ai_generator, mock_anthropic_client):
        """Test that system prompt doesn't include history section when no history"""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]

        mock_anthropic_client.messages.create.return_value = mock_response

        ai_generator.generate_response(query="Test", conversation_history=None)

        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert "Previous conversation:" not in call_args['system']

    def test_generate_response_system_prompt_format(self, ai_generator, mock_anthropic_client):
        """Test that system prompt is properly formatted"""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]

        mock_anthropic_client.messages.create.return_value = mock_response

        ai_generator.generate_response(query="Test")

        call_args = mock_anthropic_client.messages.create.call_args[1]
        system_content = call_args['system']

        # Verify system prompt includes key elements
        assert "AI assistant" in system_content or "assistant" in system_content.lower()
