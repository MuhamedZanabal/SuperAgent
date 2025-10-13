# SuperAgent Installation Guide

Complete installation and setup guide for the SuperAgent platform.

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/yourusername/superagent.git
cd superagent
\`\`\`

### 2. Create Virtual Environment

\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

### 3. Install Dependencies

\`\`\`bash
pip install -e .
\`\`\`

This will install SuperAgent in editable mode with all dependencies.

### 4. Verify Installation

\`\`\`bash
superagent --version
\`\`\`

## Configuration

### Initial Setup

Run the configuration wizard:

\`\`\`bash
superagent config init
\`\`\`

This will create a configuration file at `~/.superagent/config.yaml`.

### Configure LLM Providers

Add your API keys for LLM providers:

\`\`\`bash
# OpenAI
superagent config set openai.api_key "sk-..."

# Anthropic
superagent config set anthropic.api_key "sk-ant-..."

# Groq
superagent config set groq.api_key "gsk_..."
\`\`\`

Or edit the config file directly:

\`\`\`yaml
llm:
  providers:
    openai:
      api_key: "sk-..."
      default_model: "gpt-4"
    anthropic:
      api_key: "sk-ant-..."
      default_model: "claude-3-sonnet-20240229"
\`\`\`

### Environment Variables

Alternatively, use environment variables:

\`\`\`bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk_..."
\`\`\`

## Quick Start

### Interactive Chat

Start an interactive chat session:

\`\`\`bash
superagent chat
\`\`\`

### One-Shot Execution

Execute a single prompt:

\`\`\`bash
superagent run "What is the weather in San Francisco?"
\`\`\`

### List Available Models

\`\`\`bash
superagent models
\`\`\`

### Check Provider Status

\`\`\`bash
superagent providers
\`\`\`

## Advanced Configuration

### Memory Settings

Configure memory and vector store:

\`\`\`yaml
memory:
  vector_store:
    type: "chromadb"
    persist_directory: "~/.superagent/memory"
  embedding_provider: "sentence-transformers"
  embedding_model: "all-MiniLM-L6-v2"
\`\`\`

### Tool Configuration

Enable/disable tools:

\`\`\`yaml
tools:
  enabled:
    - file_operations
    - web_search
    - code_execution
  sandboxing:
    enabled: true
    allowed_paths:
      - "~/Documents"
      - "~/Downloads"
\`\`\`

### Security Settings

Configure security and permissions:

\`\`\`yaml
security:
  rbac:
    enabled: true
    default_role: "user"
  audit_logging:
    enabled: true
    log_file: "~/.superagent/audit.log"
  secrets:
    encryption_enabled: true
\`\`\`

## Development Setup

### Install Development Dependencies

\`\`\`bash
pip install -e ".[dev]"
\`\`\`

### Run Tests

\`\`\`bash
pytest
\`\`\`

### Run Tests with Coverage

\`\`\`bash
pytest --cov=superagent --cov-report=html
\`\`\`

### Code Formatting

\`\`\`bash
black superagent tests
ruff check superagent tests
\`\`\`

### Type Checking

\`\`\`bash
mypy superagent
\`\`\`

## Troubleshooting

### API Key Issues

If you get authentication errors:

1. Verify your API keys are correct
2. Check environment variables are set
3. Ensure config file has proper permissions

### Memory Issues

If ChromaDB fails to initialize:

\`\`\`bash
# Clear memory directory
rm -rf ~/.superagent/memory
# Restart SuperAgent
superagent chat
\`\`\`

### Permission Errors

If you get permission errors with tools:

1. Check sandboxing settings in config
2. Verify allowed paths include your working directory
3. Run with appropriate user permissions

## Updating

To update to the latest version:

\`\`\`bash
git pull origin main
pip install -e . --upgrade
\`\`\`

## Uninstallation

To remove SuperAgent:

\`\`\`bash
pip uninstall superagent
rm -rf ~/.superagent
\`\`\`

## Support

For issues and questions:

- GitHub Issues: https://github.com/yourusername/superagent/issues
- Documentation: https://superagent.readthedocs.io
- Community: https://discord.gg/superagent
