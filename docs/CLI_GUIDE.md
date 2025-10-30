# SuperAgent CLI Guide

## Overview

SuperAgent provides a comprehensive CLI with two modes of operation:

1. **Interactive Shell** - GeminiCLI/Codex-style experience with slash commands
2. **Command Mode** - Traditional CLI commands for scripting and automation

## Getting Started

### First Run

When you run SuperAgent for the first time, it will launch an interactive setup wizard:

\`\`\`bash
superagent
\`\`\`

The wizard will guide you through:
- API key configuration
- Model selection
- Default parameters
- Profile creation
- UI preferences
- Feature flags

### Manual Configuration

You can also run the wizard manually:

\`\`\`bash
superagent wizard
\`\`\`

Or initialize with default settings:

\`\`\`bash
superagent init
\`\`\`

## Interactive Shell

Launch the interactive shell:

\`\`\`bash
superagent
# or explicitly
superagent interactive
\`\`\`

### Slash Commands

The interactive shell supports comprehensive slash commands:

#### Session Management
- `/help` - Display all available commands
- `/clear` - Clear conversation history
- `/new` or `/reset` - Start new conversation
- `/quit` or `/exit` - Exit shell

#### Conversation History
- `/history [n]` - Show last n messages (default: all)
- `/search <query>` - Search within conversation
- `/undo` - Remove last message
- `/redo` - Resend last message

#### File Operations
- `/save <filename>` - Save conversation to JSON
- `/load <filename>` - Load previous conversation
- `/export <format>` - Export as txt, md, html, or pdf

#### Configuration
- `/model [name]` - Switch between models
- `/temp <value>` - Adjust temperature (0.0-1.0)
- `/tokens <num>` - Set max tokens
- `/system <prompt>` - Set system prompt
- `/profile <name>` - Switch profiles
- `/config` - Display current configuration

#### Advanced Features
- `/streaming [on|off]` - Toggle streaming responses
- `/multiline` - Enter multiline input mode
- `/file <path>` - Attach file with context
- `/image <path>` - Analyze image
- `/code <language>` - Request code in specific language
- `/web <url>` - Fetch and analyze web content
- `/summarize` - Summarize conversation
- `/continue` - Continue from last response
- `/regenerate` - Regenerate last response

#### Utilities
- `/stats` - Show conversation statistics
- `/copy [n]` - Copy response to clipboard
- `/edit [n]` - Edit previous message
- `/branch [n]` - Create conversation branch

### Features

#### Auto-Save
Conversations are automatically saved after each exchange (configurable).

#### Context Files
Use `@` to mention files and include them in context:

\`\`\`
@src/main.py explain this code
\`\`\`

#### Syntax Highlighting
Code blocks in responses are automatically syntax highlighted.

#### Cost Tracking
Token usage and estimated costs are tracked per conversation.

#### Session Persistence
Sessions are automatically saved and can be resumed later.

## Command Mode

### Chat Command

Quick one-off conversations:

\`\`\`bash
superagent chat "Explain quantum computing"
\`\`\`

With options:

\`\`\`bash
superagent chat "Write a Python function" \
  --model claude-sonnet-4 \
  --temperature 0.7 \
  --max-tokens 2000
\`\`\`

### Run Command

Execute tasks with full context:

\`\`\`bash
superagent run "Analyze this codebase" \
  --context src/ \
  --output analysis.md
\`\`\`

### Configuration Commands

View configuration:

\`\`\`bash
superagent config show
\`\`\`

Set configuration values:

\`\`\`bash
superagent config set default_model claude-opus-4
superagent config set temperature 0.8
\`\`\`

### Provider Commands

List available providers:

\`\`\`bash
superagent providers
\`\`\`

Test provider connection:

\`\`\`bash
superagent providers test anthropic
\`\`\`

### Model Commands

List available models:

\`\`\`bash
superagent models
\`\`\`

Get model details:

\`\`\`bash
superagent models info claude-sonnet-4
\`\`\`

## Profiles

Profiles allow you to maintain different configurations for different use cases.

### Creating Profiles

During wizard setup or manually in config:

\`\`\`yaml
profiles:
  default:
    temperature: 1.0
    max_tokens: 4096
    system_prompt: null
  
  coding:
    temperature: 0.7
    max_tokens: 8000
    system_prompt: "You are an expert programmer..."
  
  creative:
    temperature: 1.2
    max_tokens: 4096
    system_prompt: "You are a creative writing assistant..."
\`\`\`

### Switching Profiles

In interactive shell:

\`\`\`
/profile coding
\`\`\`

In command mode:

\`\`\`bash
superagent chat "Write a function" --profile coding
\`\`\`

## Configuration File

Configuration is stored in `~/.superagent/config.yaml`:

\`\`\`yaml
# API Keys (encrypted)
anthropic_api_key: "encrypted_key_here"

# Default Settings
default_provider: anthropic
default_model: claude-sonnet-4-20250514
temperature: 1.0
max_tokens: 4096

# Profiles
profiles:
  default:
    temperature: 1.0
    max_tokens: 4096

# UI Preferences
ui_preferences:
  color_scheme: dark
  syntax_highlighting: true
  streaming: true
  show_tokens: true
  show_cost: true

# Features
features:
  auto_save: true
  cost_tracking: true
  web_search: false
  code_execution: false
\`\`\`

## Environment Variables

Override configuration with environment variables:

\`\`\`bash
export SUPERAGENT_ANTHROPIC_API_KEY="sk-ant-..."
export SUPERAGENT_DEFAULT_MODEL="claude-opus-4"
export SUPERAGENT_TEMPERATURE="0.8"
export SUPERAGENT_DEBUG="true"
\`\`\`

## Tips & Tricks

### Keyboard Shortcuts

- `Ctrl+C` - Interrupt current operation
- `Ctrl+D` - Exit shell (same as `/quit`)
- `Up/Down` - Navigate command history
- `Tab` - Autocomplete slash commands

### Multiline Input

For long prompts, use multiline mode:

\`\`\`
/multiline
\`\`\`

Then type your prompt across multiple lines. Press `Ctrl+D` when done.

### File Context

Include multiple files:

\`\`\`
@src/main.py @src/utils.py @README.md
Explain how these files work together
\`\`\`

### Cost Management

Monitor costs in real-time:

\`\`\`
/stats
\`\`\`

Set token limits to control costs:

\`\`\`
/tokens 1000
\`\`\`

### Conversation Branching

Explore alternative responses:

\`\`\`
/branch 5
\`\`\`

This creates a new conversation branch from message #5.

## Troubleshooting

### API Key Issues

If you see authentication errors:

1. Check your API key: `/config`
2. Verify key is valid: `superagent providers test anthropic`
3. Re-run wizard: `superagent wizard`

### Performance Issues

If responses are slow:

1. Check your internet connection
2. Try a faster model: `/model claude-3-5-haiku`
3. Reduce max tokens: `/tokens 2000`

### Configuration Issues

Reset configuration:

\`\`\`bash
rm ~/.superagent/config.yaml
superagent wizard
\`\`\`

## Advanced Usage

### Scripting

Use SuperAgent in scripts:

\`\`\`bash
#!/bin/bash

# Generate code
superagent run "Create a REST API" --output api.py

# Review code
superagent run "Review this code" --context api.py --output review.md

# Run tests
python api.py
\`\`\`

### CI/CD Integration

\`\`\`yaml
# .github/workflows/ai-review.yml
- name: AI Code Review
  run: |
    superagent run "Review this PR" \
      --context ${{ github.event.pull_request.diff_url }} \
      --output review.md
\`\`\`

### Custom Profiles

Create specialized profiles for your workflow:

\`\`\`yaml
profiles:
  code_review:
    temperature: 0.5
    max_tokens: 6000
    system_prompt: |
      You are a senior code reviewer. Focus on:
      - Security vulnerabilities
      - Performance issues
      - Code quality and maintainability
      - Best practices
\`\`\`

## Support

For issues or questions:

- GitHub: https://github.com/yourusername/superagent
- Documentation: https://superagent.dev/docs
- Discord: https://discord.gg/superagent
