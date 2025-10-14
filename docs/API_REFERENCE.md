# SuperAgent API Reference

## Core Runtime

### SuperAgentRuntime

Main runtime coordinator for all subsystems.

\`\`\`python
from superagent.core.runtime import SuperAgentRuntime

runtime = SuperAgentRuntime()
await runtime.initialize()

# Use runtime
response = await runtime.llm_provider.generate(request)

# Cleanup
await runtime.cleanup()
\`\`\`

#### Methods

- `initialize()` - Initialize all subsystems
- `cleanup()` - Cleanup resources
- `get_status()` - Get runtime status

## LLM Provider

### Creating Providers

\`\`\`python
from superagent.llm import create_default_provider
from superagent.llm.models import LLMRequest, Message

provider = create_default_provider()

request = LLMRequest(
    model="gpt-4",
    messages=[
        Message(role="user", content="Hello")
    ],
    temperature=0.7,
)

response = await provider.generate(request)
\`\`\`

### Streaming

\`\`\`python
async for chunk in provider.stream(request):
    print(chunk.delta, end="")
\`\`\`

## Memory System

### Storing Memories

\`\`\`python
from superagent.memory.manager import MemoryManager
from superagent.memory.models import MemoryItem, MemoryType

manager = MemoryManager()
await manager.initialize()

item = MemoryItem(
    content="Important information",
    memory_type=MemoryType.LONG_TERM,
    metadata={"source": "user"},
)

await manager.store(item)
\`\`\`

### Searching Memories

\`\`\`python
from superagent.memory.models import MemoryQuery

query = MemoryQuery(
    query="important information",
    limit=10,
    memory_types=[MemoryType.LONG_TERM],
)

results = await manager.search(query)
\`\`\`

## Tool System

### Registering Tools

\`\`\`python
from superagent.tools.registry import ToolRegistry
from superagent.tools.base import BaseTool

registry = ToolRegistry()

class CustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "custom_tool"
    
    async def execute(self, **kwargs):
        # Implementation
        pass

registry.register(CustomTool())
\`\`\`

### Executing Tools

\`\`\`python
from superagent.tools.executor import ToolExecutor
from superagent.tools.models import ToolCall

executor = ToolExecutor()

call = ToolCall(
    tool_name="read_file",
    parameters={"path": "file.txt"},
)

result = await executor.execute(call)
\`\`\`

## Agent System

### Creating Agents

\`\`\`python
from superagent.agents.react_agent import ReActAgent
from superagent.agents.models import AgentConfig

config = AgentConfig(
    max_iterations=10,
    timeout=300,
)

agent = ReActAgent(
    llm_provider=provider,
    tool_registry=registry,
    config=config,
)

result = await agent.execute("Complete this task")
\`\`\`

## Orchestration

### Event Bus

\`\`\`python
from superagent.orchestration.event_bus import EventBus, Event

bus = EventBus()

# Subscribe to events
async def handler(event: Event):
    print(f"Received: {event.type}")

bus.subscribe("task.completed", handler)

# Publish events
await bus.publish(Event(
    type="task.completed",
    data={"result": "success"},
))
\`\`\`

### Orchestrator

\`\`\`python
from superagent.orchestration.orchestrator import Orchestrator

orchestrator = Orchestrator(runtime)

result = await orchestrator.execute_goal(
    goal="Analyze data and generate report",
    timeout=600,
)
\`\`\`

## Configuration

### Loading Configuration

\`\`\`python
from superagent.core.config import SuperAgentConfig

config = SuperAgentConfig()

# Access settings
print(config.default_model)
print(config.temperature)
\`\`\`

### Environment Variables

\`\`\`bash
SUPERAGENT_DEFAULT_MODEL=gpt-4
SUPERAGENT_TEMPERATURE=0.7
SUPERAGENT_MAX_TOKENS=2048
OPENAI_API_KEY=sk-...
\`\`\`

## Security

### Permission Management

\`\`\`python
from superagent.core.security import SecurityManager, Permission

security = SecurityManager()

# Validate file access
security.validate_file_access(path, Permission.READ)

# Encrypt data
encrypted = security.encrypt("sensitive data")
decrypted = security.decrypt(encrypted)
\`\`\`

## Monitoring

### Metrics

\`\`\`python
from superagent.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

# Record metrics
metrics.increment_counter("requests.total")
metrics.record_histogram("request.duration", 0.5)
\`\`\`

### Health Checks

\`\`\`python
from superagent.monitoring.health import HealthChecker

health = HealthChecker(runtime)
status = await health.check_all()

print(status.overall_health)  # "healthy" | "degraded" | "unhealthy"
\`\`\`

## Error Handling

### Custom Exceptions

\`\`\`python
from superagent.core.exceptions import (
    SuperAgentError,
    LLMProviderError,
    ToolExecutionError,
)

try:
    result = await provider.generate(request)
except LLMProviderError as e:
    print(f"Provider error: {e}")
except SuperAgentError as e:
    print(f"General error: {e}")
\`\`\`

## Type Definitions

### Common Types

\`\`\`python
from typing import List, Optional
from superagent.llm.models import Message, LLMResponse
from superagent.tools.models import ToolResult
from superagent.memory.models import MemoryItem
\`\`\`

## Examples

See `examples/` directory for complete examples:
- `basic_chat.py` - Simple chat interaction
- `tool_usage.py` - Using tools
- `memory_demo.py` - Memory system
- `agent_workflow.py` - Agent execution
