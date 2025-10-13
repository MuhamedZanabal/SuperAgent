# SuperAgent CLI Usage Guide

## Installation

\`\`\`bash
pip install -e .
\`\`\`

## Quick Start

### Initialize Configuration

\`\`\`bash
superagent init
\`\`\`

This creates a configuration file at `~/.superagent/config.yaml`. Edit this file to add your API keys:

\`\`\`yaml
openai_api_key: "sk-..."
anthropic_api_key: "sk-ant-..."
groq_api_key: "gsk_..."
\`\`\`

### Check Provider Status

\`\`\`bash
superagent providers
\`\`\`

Shows all configured providers and their status.

### List Available Models

\`\`\`bash
superagent models
\`\`\`

List all available models across all providers.

## Commands

### Interactive Chat

Start an interactive chat session:

\`\`\`bash
superagent chat
\`\`\`

With options:

\`\`\`bash
superagent chat --model gpt-4-turbo-preview
superagent chat --system "You are a helpful coding assistant"
superagent chat --temperature 0.9
superagent chat --no-stream  # Disable streaming
\`\`\`

Chat commands:
- `exit` or `quit` - End the session
- `clear` - Clear conversation history
- `save` - Save conversation to file

### One-Shot Execution

Execute a single prompt:

\`\`\`bash
superagent run "Explain quantum computing"
\`\`\`

With options:

\`\`\`bash
superagent run "Write a Python function" --model gpt-4
superagent run "Analyze this data" --system "You are a data analyst"
superagent run "Generate code" --output result.txt
superagent run "Complex task" --max-tokens 2000 --temperature 0.7
\`\`\`

### Configuration Management

Show current configuration:

\`\`\`bash
superagent config --show
\`\`\`

Set configuration values:

\`\`\`bash
superagent config --set default_model=gpt-4
superagent config --set temperature=0.8
\`\`\`

Export configuration:

\`\`\`bash
superagent config --export my-config.yaml
\`\`\`

### Version Information

\`\`\`bash
superagent version
\`\`\`

## Global Options

All commands support these global options:

- `--config PATH` - Use custom configuration file
- `--debug` - Enable debug mode
- `--verbose` - Enable verbose output

Example:

\`\`\`bash
superagent --debug --config custom.yaml chat
\`\`\`

## Environment Variables

You can also configure SuperAgent using environment variables:

\`\`\`bash
export SUPERAGENT_OPENAI_API_KEY="sk-..."
export SUPERAGENT_DEFAULT_MODEL="gpt-4-turbo-preview"
export SUPERAGENT_TEMPERATURE="0.7"
export SUPERAGENT_MAX_TOKENS="4096"
export SUPERAGENT_DEBUG="true"
\`\`\`

## Examples

### Basic Chat

\`\`\`bash
superagent chat
\`\`\`

### Code Generation

\`\`\`bash
superagent run "Write a Python function to calculate fibonacci numbers" \
  --system "You are an expert Python developer" \
  --output fibonacci.py
\`\`\`

### Data Analysis

\`\`\`bash
superagent chat --model gpt-4 --system "You are a data scientist"
\`\`\`

### Quick Questions

\`\`\`bash
superagent run "What is the capital of France?"
\`\`\`

### Using Different Providers

\`\`\`bash
# Use Claude
superagent run "Explain AI" --model claude-3-opus-20240229

# Use Groq (fast inference)
superagent run "Quick question" --model llama-3.1-70b-versatile

# Use local Ollama
superagent run "Test prompt" --model llama3.1
\`\`\`

## Tips

1. **Streaming**: Streaming is enabled by default for real-time responses. Disable with `--no-stream` if you prefer to wait for the complete response.

2. **System Prompts**: Use system prompts to set the assistant's behavior and expertise.

3. **Temperature**: Lower values (0.1-0.3) for factual tasks, higher values (0.7-1.0) for creative tasks.

4. **Model Selection**: Choose models based on your needs:
   - GPT-4: Best quality, slower, more expensive
   - GPT-3.5: Fast, cheap, good for simple tasks
   - Claude: Great for long contexts and analysis
   - Groq: Extremely fast inference
   - Ollama: Free, local, private

5. **Save Conversations**: Use the `save` command in chat mode to keep important conversations.

## Troubleshooting

### Provider Not Configured

\`\`\`
Error: Provider not configured
\`\`\`

Solution: Add API key to config file or environment variable.

### Model Not Found

\`\`\`
Error: No provider found for model
\`\`\`

Solution: Check available models with `superagent models`.

### Rate Limiting

The system automatically retries with exponential backoff and falls back to alternative providers when available.
