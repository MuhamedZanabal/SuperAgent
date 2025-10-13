# SuperAgent

A production-ready, CLI-based AI automation platform for orchestrating large language models, tools, and workflows at scale.

## Features

- **Multi-Provider LLM Support**: Unified interface for OpenAI, Anthropic, Groq, Together, OpenRouter, Ollama, and more
- **Automatic Fallback**: Intelligent provider switching on failures
- **Streaming Support**: Real-time response streaming with callbacks
- **Hierarchical Memory**: Short-term, working, and long-term memory with vector search
- **Tool Orchestration**: Dynamic tool loading with sandboxed execution
- **Autonomous Agents**: ReAct pattern with multi-step reasoning and planning
- **Security First**: Sandboxed execution, encrypted configs, RBAC, audit logging
- **Monitoring & Analytics**: Comprehensive metrics, telemetry, and cost tracking
- **Production Ready**: Extensive logging, error handling, and health checks

## Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/yourusername/superagent.git
cd superagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with pip
pip install -e .

# Verify installation
superagent --version
\`\`\`

## Quick Start

### CLI Usage

\`\`\`bash
# Interactive chat
superagent chat

# One-shot execution
superagent run "What is the weather in San Francisco?"

# List available models
superagent models

# Check provider status
superagent providers

# Configure settings
superagent config set openai.api_key "sk-..."
\`\`\`

### Python API

\`\`\`python
from superagent.llm import create_default_provider
from superagent.llm.models import LLMRequest, Message
from superagent.core.config import SuperAgentConfig

# Configure
config = SuperAgentConfig(
    openai_api_key="your-api-key",
    default_model="gpt-4",
)

# Create provider
provider = create_default_provider(config)

# Generate completion
request = LLMRequest(
    model="gpt-4",
    messages=[
        Message(role="user", content="Hello, how are you?")
    ],
)

response = await provider.generate(request)
print(response.content)
\`\`\`

### Using Agents

\`\`\`python
from superagent.agents import ReActAgent
from superagent.llm import create_default_provider
from superagent.memory import MemoryManager
from superagent.tools import ToolRegistry

# Initialize components
llm = create_default_provider(config)
memory = MemoryManager()
tools = ToolRegistry()

# Create agent
agent = ReActAgent(
    llm_provider=llm,
    memory_manager=memory,
    tool_registry=tools,
)

# Execute task
result = await agent.execute("Search for Python tutorials and summarize the top 3")
print(result.output)
\`\`\`

## Configuration

### Environment Variables

\`\`\`bash
# LLM Provider API Keys
SUPERAGENT_OPENAI_API_KEY=your-openai-key
SUPERAGENT_ANTHROPIC_API_KEY=your-anthropic-key
SUPERAGENT_GROQ_API_KEY=your-groq-key
SUPERAGENT_TOGETHER_API_KEY=your-together-key
SUPERAGENT_OPENROUTER_API_KEY=your-openrouter-key

# Configuration
SUPERAGENT_DEFAULT_MODEL=gpt-4
SUPERAGENT_MAX_TOKENS=4096
SUPERAGENT_TEMPERATURE=0.7
SUPERAGENT_DEBUG=false
\`\`\`

### Config File

Create `~/.superagent/config.yaml`:

\`\`\`yaml
llm:
  providers:
    openai:
      api_key: "sk-..."
      default_model: "gpt-4"
    anthropic:
      api_key: "sk-ant-..."
      default_model: "claude-3-sonnet-20240229"
  
memory:
  vector_store:
    type: "chromadb"
    persist_directory: "~/.superagent/memory"
  
tools:
  sandboxing:
    enabled: true
    allowed_paths:
      - "~/Documents"
      - "~/Downloads"

security:
  rbac:
    enabled: true
    default_role: "user"
  audit_logging:
    enabled: true
\`\`\`

## Architecture

\`\`\`
superagent/
├── core/           # Core runtime, config, logging, security
├── llm/            # LLM provider layer with unified interface
├── memory/         # Hierarchical memory and vector stores
├── agents/         # Agent orchestration and planning
├── tools/          # Tool and plugin system
├── cli/            # CLI interface with Rich UI
├── security/       # RBAC, audit logging, secrets management
└── monitoring/     # Metrics, telemetry, health checks, analytics
\`\`\`

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [CLI Usage](docs/CLI_USAGE.md)
- [Monitoring & Security](docs/MONITORING.md)

## Development

\`\`\`bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=superagent --cov-report=html

# Format code
black superagent tests
ruff check superagent tests

# Type checking
mypy superagent
\`\`\`

## Key Components

### LLM Provider Manager
- Unified interface for 100+ models via LiteLLM
- Automatic fallback between providers
- Streaming support with callbacks
- Token counting and cost tracking

### Memory Systems
- Hierarchical memory (short-term, working, long-term)
- Vector store integration with ChromaDB
- Semantic search and retrieval
- Context window management

### Tool System
- Dynamic tool loading and registration
- Sandboxed execution with timeouts
- Built-in tools: file ops, web scraping, code execution
- Function calling integration

### Agent Framework
- ReAct pattern implementation
- Multi-step planning and execution
- Tool orchestration and chaining
- Reflection and error correction

### Monitoring
- Metrics: counters, gauges, histograms, timers
- Telemetry: event tracking and session management
- Health checks: component monitoring
- Analytics: usage stats and cost analysis

### Security
- RBAC: role-based access control
- Audit logging: security event tracking
- Secrets management: encrypted storage and rotation
- Sandboxing: isolated execution environments

## Examples

See the `examples/` directory for complete examples:

- `basic_chat.py` - Simple chat interaction
- `agent_workflow.py` - Multi-step agent execution
- `tool_usage.py` - Using tools with agents
- `memory_demo.py` - Memory and context management
- `monitoring.py` - Metrics and analytics

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

- GitHub Issues: https://github.com/yourusername/superagent/issues
- Documentation: https://superagent.readthedocs.io
- Community: https://discord.gg/superagent
