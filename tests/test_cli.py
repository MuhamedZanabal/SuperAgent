"""
Tests for CLI interface.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from superagent.cli.app import app
from superagent.core.config import SuperAgentConfig

runner = CliRunner()


def test_version_command():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "SuperAgent" in result.stdout
    assert "v0.1.0" in result.stdout


def test_init_command(tmp_path):
    """Test init command."""
    config_file = tmp_path / "config.yaml"
    
    result = runner.invoke(app, ["init", "--output", str(config_file)])
    assert result.exit_code == 0
    assert config_file.exists()
    assert "Configuration initialized" in result.stdout


def test_config_show_command():
    """Test config show command."""
    result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "SuperAgent Configuration" in result.stdout
    assert "Core Settings" in result.stdout


def test_models_command():
    """Test models command."""
    with patch("superagent.cli.models.create_default_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.list_available_models.return_value = [
            "gpt-4-turbo-preview",
            "claude-3-opus-20240229",
        ]
        mock_instance.get_provider_for_model.return_value = "openai"
        mock_provider.return_value = mock_instance
        
        result = runner.invoke(app, ["models"])
        assert result.exit_code == 0
        assert "Available Models" in result.stdout


def test_providers_command():
    """Test providers command."""
    with patch("superagent.cli.providers.create_default_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.list_providers.return_value = ["openai", "anthropic"]
        mock_instance.get_all_metrics.return_value = {
            "openai": {
                "total_requests": 10,
                "successful_requests": 9,
                "failed_requests": 1,
                "success_rate": 0.9,
                "total_tokens": 1000,
                "total_cost": 0.05,
                "avg_latency_ms": 250.0,
            }
        }
        mock_provider.return_value = mock_instance
        
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "Provider Status" in result.stdout


def test_debug_flag():
    """Test debug flag."""
    result = runner.invoke(app, ["--debug", "version"])
    assert result.exit_code == 0


def test_config_file_loading(tmp_path):
    """Test loading configuration from file."""
    config_file = tmp_path / "config.yaml"
    
    # Create a config file
    config = SuperAgentConfig()
    config.to_yaml(config_file)
    
    result = runner.invoke(app, ["--config", str(config_file), "version"])
    assert result.exit_code == 0
