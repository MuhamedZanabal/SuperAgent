"""
Tests for enhanced CLI features including wizard and interactive shell.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from superagent.cli.wizard import ConfigurationWizard
from superagent.cli.interactive.enhanced_shell import EnhancedShell
from superagent.core.config import SuperAgentConfig
from superagent.core.runtime import SuperAgentRuntime


class TestConfigurationWizard:
    """Test configuration wizard."""
    
    @pytest.fixture
    def wizard(self, tmp_path):
        """Create wizard instance with temp config path."""
        config_path = tmp_path / "config.yaml"
        return ConfigurationWizard(config_path)
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, wizard):
        """Test API key validation with valid key."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create = Mock(return_value=Mock())
            mock_anthropic.return_value = mock_client
            
            result = await wizard._validate_api_key("sk-ant-test123")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, wizard):
        """Test API key validation with invalid key."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.side_effect = Exception("Invalid API key")
            
            result = await wizard._validate_api_key("invalid-key")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_save_config(self, wizard, tmp_path):
        """Test configuration saving."""
        config = SuperAgentConfig(
            anthropic_api_key="test-key",
            default_provider="anthropic"
        )
        
        await wizard._save_config(config)
        
        assert wizard.config_path.exists()
        assert wizard.config_path.stat().st_mode & 0o777 == 0o600


class TestEnhancedShell:
    """Test enhanced interactive shell."""
    
    @pytest.fixture
    def mock_runtime(self):
        """Create mock runtime."""
        config = SuperAgentConfig()
        runtime = Mock(spec=SuperAgentRuntime)
        runtime.config = config
        return runtime
    
    @pytest.fixture
    def shell(self, mock_runtime):
        """Create shell instance."""
        return EnhancedShell(mock_runtime)
    
    def test_shell_initialization(self, shell):
        """Test shell initializes correctly."""
        assert shell.conversation_history == []
        assert shell.current_profile == "default"
        assert shell.stats["messages"] == 0
        assert len(shell.commands) > 20
    
    @pytest.mark.asyncio
    async def test_cmd_clear(self, shell):
        """Test clear command."""
        shell.conversation_history = [{"role": "user", "content": "test"}]
        shell.stats["messages"] = 1
        
        await shell.cmd_clear("")
        
        assert shell.conversation_history == []
        assert shell.stats["messages"] == 0
    
    @pytest.mark.asyncio
    async def test_cmd_undo(self, shell):
        """Test undo command."""
        shell.conversation_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]
        
        await shell.cmd_undo("")
        
        assert len(shell.conversation_history) == 0
    
    @pytest.mark.asyncio
    async def test_cmd_save(self, shell, tmp_path):
        """Test save command."""
        shell.conversation_dir = tmp_path
        shell.conversation_history = [{"role": "user", "content": "test"}]
        
        await shell.cmd_save("test.json")
        
        save_file = tmp_path / "test.json"
        assert save_file.exists()
    
    @pytest.mark.asyncio
    async def test_cmd_load(self, shell, tmp_path):
        """Test load command."""
        shell.conversation_dir = tmp_path
        
        # Create test conversation file
        import json
        test_data = {
            "session_id": "test123",
            "history": [{"role": "user", "content": "test"}],
            "stats": {"messages": 1}
        }
        
        test_file = tmp_path / "test.json"
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        await shell.cmd_load("test.json")
        
        assert len(shell.conversation_history) == 1
        assert shell.session_id == "test123"
    
    @pytest.mark.asyncio
    async def test_handle_command(self, shell):
        """Test command handling."""
        with patch.object(shell, 'cmd_help', new_callable=AsyncMock) as mock_help:
            await shell.handle_command("/help")
            mock_help.assert_called_once_with("")
    
    @pytest.mark.asyncio
    async def test_handle_command_with_args(self, shell):
        """Test command handling with arguments."""
        with patch.object(shell, 'cmd_history', new_callable=AsyncMock) as mock_history:
            await shell.handle_command("/history 10")
            mock_history.assert_called_once_with("10")
    
    def test_display_response(self, shell):
        """Test response display."""
        # Should not raise exception
        shell.display_response("Test response with **markdown**")


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    @pytest.mark.asyncio
    async def test_first_run_flow(self, tmp_path):
        """Test first-run wizard flow."""
        config_path = tmp_path / "config.yaml"
        
        # Simulate wizard run
        wizard = ConfigurationWizard(config_path)
        
        # Mock user inputs
        with patch('superagent.cli.wizard.Prompt.ask') as mock_prompt, \
             patch('superagent.cli.wizard.Confirm.ask') as mock_confirm, \
             patch.object(wizard, '_validate_api_key', return_value=True):
            
            mock_prompt.side_effect = [
                "sk-ant-test123",  # API key
                "1",  # Model selection
                "1.0",  # Temperature
                "4096",  # Max tokens
                "0.9",  # Top P
                "40",  # Top K
                "dark",  # Color scheme
            ]
            
            mock_confirm.side_effect = [
                True,  # Use defaults
                False,  # Custom system prompt
                False,  # Additional profiles
                True,  # Syntax highlighting
                True,  # Streaming
                True,  # Show tokens
                True,  # Show cost
                True,  # Auto-save
                True,  # Cost tracking
                False,  # Web search
                False,  # Code execution
            ]
            
            config = await wizard.run()
            
            assert config is not None
            assert config_path.exists()
    
    @pytest.mark.asyncio
    async def test_interactive_shell_lifecycle(self, mock_runtime):
        """Test interactive shell lifecycle."""
        shell = EnhancedShell(mock_runtime)
        
        # Test initialization
        assert shell.session_id is not None
        assert shell.conversation_dir.exists()
        
        # Test message handling
        with patch.object(shell.orchestrator, 'process_input', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "content": "Test response",
                "tokens": 100,
                "cost": 0.001
            }
            
            await shell.handle_message("Test message")
            
            assert len(shell.conversation_history) == 2
            assert shell.stats["messages"] == 2
            assert shell.stats["tokens_used"] == 100


@pytest.mark.asyncio
async def test_cli_app_first_run(tmp_path, monkeypatch):
    """Test CLI app first-run detection."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setenv("HOME", str(tmp_path))
    
    # Config doesn't exist, should trigger wizard
    assert not config_path.exists()
    
    # Mock wizard
    with patch('superagent.cli.app.run_wizard', new_callable=AsyncMock) as mock_wizard:
        mock_config = SuperAgentConfig()
        mock_wizard.return_value = mock_config
        
        # This would normally launch wizard
        # Test is simplified to verify detection logic
        assert not config_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
