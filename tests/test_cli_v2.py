"""
Comprehensive tests for SuperAgent v2.0.0 CLI features.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from superagent.cli.conversation_manager import ConversationManager, CostTracker
from superagent.cli.file_handler import FileHandler
from superagent.cli.clipboard import ClipboardManager
from superagent.plugins.registry import PluginRegistry
from superagent.plugins.base import Plugin, PluginMetadata
from superagent.automation.scheduler import Scheduler, Schedule, ScheduleType


class TestConversationManager:
    """Test conversation management."""
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading conversations."""
        manager = ConversationManager(tmp_path)
        
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        metadata = {"profile": "default"}
        
        # Save
        filepath = manager.save("test_session", history, metadata)
        assert filepath.exists()
        
        # Load
        data = manager.load(filepath.name)
        assert data["session_id"] == "test_session"
        assert len(data["history"]) == 2
    
    def test_search(self):
        """Test conversation search."""
        manager = ConversationManager()
        
        history = [
            {"role": "user", "content": "Tell me about Python"},
            {"role": "assistant", "content": "Python is a programming language"},
            {"role": "user", "content": "What about JavaScript?"}
        ]
        
        results = manager.search("python", history)
        assert len(results) == 2  # Found in both messages
    
    def test_branch(self):
        """Test conversation branching."""
        manager = ConversationManager()
        
        history = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"}
        ]
        
        branched = manager.branch(history, 1, "new_session")
        assert len(branched) == 2
    
    def test_export_formats(self, tmp_path):
        """Test exporting in different formats."""
        manager = ConversationManager(tmp_path)
        
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
        
        # Test text export
        txt_content = manager.export_text(history)
        assert "USER" in txt_content
        assert "Hello" in txt_content
        
        # Test markdown export
        md_content = manager.export_markdown(history)
        assert "# Conversation" in md_content
        assert "## User" in md_content
        
        # Test HTML export
        html_content = manager.export_html(history)
        assert "<!DOCTYPE html>" in html_content
        assert "Hello" in html_content


class TestCostTracker:
    """Test cost tracking."""
    
    def test_track_usage(self):
        """Test tracking token usage and costs."""
        tracker = CostTracker()
        
        cost = tracker.track("claude-sonnet-4-20250514", 1000, 500)
        assert cost > 0
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
    
    def test_get_stats(self):
        """Test getting usage statistics."""
        tracker = CostTracker()
        
        tracker.track("claude-sonnet-4-20250514", 1000, 500)
        tracker.track("claude-3-5-haiku-20241022", 2000, 1000)
        
        stats = tracker.get_stats()
        assert stats["total_input_tokens"] == 3000
        assert stats["total_output_tokens"] == 1500
        assert len(stats["model_usage"]) == 2


class TestFileHandler:
    """Test file handling."""
    
    def test_read_text_file(self, tmp_path):
        """Test reading text files."""
        handler = FileHandler()
        
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello')")
        
        result = handler.read_file(str(test_file))
        assert result["type"] == "text"
        assert "Hello" in result["content"]
    
    def test_file_size_limit(self, tmp_path):
        """Test file size limit."""
        handler = FileHandler()
        
        # Create large file
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * (handler.MAX_FILE_SIZE + 1))
        
        with pytest.raises(ValueError, match="File too large"):
            handler.read_file(str(large_file))
    
    def test_unsupported_file_type(self, tmp_path):
        """Test unsupported file types."""
        handler = FileHandler()
        
        test_file = tmp_path / "test.exe"
        test_file.write_bytes(b"binary data")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            handler.read_file(str(test_file))


class TestPluginSystem:
    """Test plugin system."""
    
    def test_register_plugin(self):
        """Test plugin registration."""
        registry = PluginRegistry()
        
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            dependencies=[],
            entry_point="test:TestPlugin"
        )
        
        class TestPlugin(Plugin):
            async def initialize(self, runtime):
                pass
            
            async def execute(self, context):
                return {"result": "success"}
            
            async def cleanup(self):
                pass
        
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        
        assert registry.get("test_plugin") == plugin
        assert len(registry.list_plugins()) == 1
    
    def test_list_enabled_plugins(self):
        """Test listing enabled plugins."""
        registry = PluginRegistry()
        
        # Add enabled plugin
        metadata1 = PluginMetadata(
            name="plugin1",
            version="1.0.0",
            description="Plugin 1",
            author="Test",
            dependencies=[],
            entry_point="test:Plugin1",
            enabled=True
        )
        
        # Add disabled plugin
        metadata2 = PluginMetadata(
            name="plugin2",
            version="1.0.0",
            description="Plugin 2",
            author="Test",
            dependencies=[],
            entry_point="test:Plugin2",
            enabled=False
        )
        
        class TestPlugin(Plugin):
            async def initialize(self, runtime):
                pass
            async def execute(self, context):
                return {}
            async def cleanup(self):
                pass
        
        registry.register(TestPlugin(metadata1))
        registry.register(TestPlugin(metadata2))
        
        enabled = registry.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].metadata.name == "plugin1"


class TestScheduler:
    """Test task scheduler."""
    
    @pytest.mark.asyncio
    async def test_add_schedule(self):
        """Test adding schedules."""
        scheduler = Scheduler()
        
        async def test_task():
            pass
        
        schedule = Schedule(
            id="test_schedule",
            type=ScheduleType.ONCE,
            task=test_task,
            args={}
        )
        
        scheduler.add_schedule(schedule)
        assert scheduler.get_schedule("test_schedule") == schedule
    
    @pytest.mark.asyncio
    async def test_scheduler_lifecycle(self):
        """Test scheduler start/stop."""
        scheduler = Scheduler()
        
        await scheduler.start()
        assert scheduler._running
        
        await scheduler.stop()
        assert not scheduler._running


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow from input to output."""
    # This would test the full CLI workflow
    # Including: input -> intent routing -> execution -> output
    pass
