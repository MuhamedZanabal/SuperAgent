# SuperAgent UX Specification
## GeminiCLI/Codex-Grade Developer Experience

**Version:** 2.0  
**Status:** Implementation Ready  
**Last Updated:** 2025-01-14

---

## Executive Summary

SuperAgent 2.0 delivers a calm, minimal, anticipatory CLI experience that merges Codex-like intent understanding with GeminiCLI-style workflow integration. The UX is TTY-native yet polished, with micro-interactions, predictable motion, and enterprise-grade safety.

### Design Principles

1. **Zero Friction** - Natural language commands resolve to tasks automatically
2. **Diff-First** - All changes previewed before application
3. **Safety by Default** - RBAC gates, tool scopes, explicit consent
4. **Anticipatory** - Context-aware suggestions and completions
5. **Calm & Minimal** - Apple-inspired aesthetics with purposeful motion
6. **Accessible** - Screen reader support, high contrast, keyboard-first

---

## Architecture Overview

\`\`\`mermaid
graph TB
    Input[User Input] --> Parser[NL Parser]
    Parser --> Router[Intent Router]
    Router --> Question[Question Handler]
    Router --> Task[Task Handler]
    Router --> Code[Code Edit Handler]
    Router --> Plan[Plan Handler]
    
    Question --> LLM[LLM Provider]
    Task --> Planner[Task Planner]
    Code --> DiffEngine[Diff Engine]
    Plan --> Orchestrator[UX Orchestrator]
    
    Planner --> Tools[Tool Executor]
    DiffEngine --> Preview[Diff Preview]
    Preview --> Apply[Apply Engine]
    
    Tools --> Render[Renderer]
    Apply --> Render
    LLM --> Render
    
    Render --> Display[Terminal Display]
    
    Orchestrator --> Memory[Session Memory]
    Orchestrator --> Checkpoint[Checkpoint Manager]
    Orchestrator --> RBAC[RBAC Engine]
\`\`\`

### State Machine

\`\`\`mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Parsing: User Input
    Parsing --> IntentResolution: Parse Complete
    IntentResolution --> Question: Confidence > 0.8
    IntentResolution --> Clarify: Confidence < 0.5
    IntentResolution --> Planning: Task Intent
    
    Clarify --> Parsing: User Response
    
    Question --> Streaming: LLM Call
    Streaming --> Idle: Complete
    
    Planning --> ToolSelection: Plan Ready
    ToolSelection --> SafetyCheck: Tools Selected
    SafetyCheck --> Executing: Approved
    SafetyCheck --> Blocked: Denied
    Blocked --> Idle
    
    Executing --> DiffPreview: File Changes
    Executing --> Idle: No Changes
    
    DiffPreview --> UserReview: Diff Ready
    UserReview --> Applying: Accept
    UserReview --> Idle: Reject
    UserReview --> PartialApply: Partial
    
    PartialApply --> Applying: Hunks Selected
    Applying --> Checkpointing: Applied
    Checkpointing --> Idle: Saved
\`\`\`

---

## Component Architecture

### 1. UX Orchestrator (`cli/ux_orchestrator.py`)

**Responsibilities:**
- State machine management
- Event bus coordination
- Context aggregation
- Session lifecycle

**Key Methods:**
\`\`\`python
async def process_input(input: str) -> Response
async def resolve_intent(input: str) -> Intent
async def execute_plan(plan: Plan) -> Result
async def checkpoint_state() -> CheckpointID
async def restore_checkpoint(id: CheckpointID) -> None
\`\`\`

**Event Flow:**
\`\`\`
Input → Parse → Route → Execute → Render → Checkpoint
  ↓       ↓       ↓        ↓         ↓          ↓
Memory  Intent  Plan    Tools    Display   Storage
\`\`\`

### 2. Intent Router (`planner/nl2task_router.py`)

**Intent Types:**
- `Question` - Information retrieval
- `Task` - Action execution (build, deploy, test)
- `CodeEdit` - File modifications
- `Plan` - Multi-step workflow
- `Meta` - System commands (/checkpoint, /theme)

**Classification Pipeline:**
\`\`\`
Input → Tokenize → Extract Entities → Score Intents → Select Best
\`\`\`

**Confidence Thresholds:**
- High (>0.8): Auto-execute
- Medium (0.5-0.8): Confirm with user
- Low (<0.5): Request clarification

### 3. Renderer (`cli/render/`)

**Components:**

#### Panel System
\`\`\`python
class Panel:
    - title: str
    - content: RenderableType
    - border_style: str
    - collapsible: bool
    - expanded: bool
\`\`\`

**Panel Types:**
- `ReasoningPanel` - LLM thought process
- `PlanPanel` - Step-by-step execution plan
- `DiffPanel` - Code changes with syntax highlighting
- `ToolPanel` - Tool execution and output
- `StatusPanel` - Progress and metrics

#### Motion & Timing
- **Spinner delay:** 90-120ms (perceptual smoothness)
- **Easing:** cubic-bezier(0.25, 0.1, 0.25, 1.0)
- **Transitions:** 200ms for panel expand/collapse
- **Debounce:** 150ms for autocomplete

#### Theme System
\`\`\`yaml
themes:
  light:
    background: "#FFFFFF"
    foreground: "#1D1D1F"
    accent: "#007AFF"
    success: "#34C759"
    warning: "#FF9500"
    error: "#FF3B30"
    
  dark:
    background: "#000000"
    foreground: "#F5F5F7"
    accent: "#0A84FF"
    success: "#30D158"
    warning: "#FF9F0A"
    error: "#FF453A"
\`\`\`

### 4. Diff Engine (`cli/diff_engine.py`)

**Workflow:**
\`\`\`
1. Generate Plan
2. Dry-run execution
3. Capture file changes
4. Create unified diffs
5. Present with context
6. Accept/Reject/Partial
7. Apply atomically
8. Checkpoint
\`\`\`

**Diff Display:**
\`\`\`
┌─ File: src/main.py ─────────────────────────────────┐
│ @@ -15,7 +15,9 @@                                    │
│   def process_data(input):                           │
│ -     return input.strip()                           │
│ +     # Validate input before processing             │
│ +     if not input:                                  │
│ +         raise ValueError("Empty input")            │
│ +     return input.strip().lower()                   │
│                                                       │
│ Risk: Low | Files: 1 | Lines: +4/-1                 │
└──────────────────────────────────────────────────────┘
\`\`\`

**Partial Apply:**
- Select hunks with arrow keys
- Space to toggle selection
- Enter to apply selected
- Esc to cancel

### 5. Safety & RBAC (`security/rbac.py`)

**Permission Model:**
\`\`\`yaml
roles:
  viewer:
    - read_files
    - ask_questions
    
  developer:
    - read_files
    - write_files
    - run_tests
    - use_safe_tools
    
  admin:
    - all_permissions
    - manage_settings
    - run_shell_commands

tool_scopes:
  safe:
    - read_file
    - search_code
    - analyze_dependencies
    
  requires_approval:
    - write_file
    - run_tests
    - install_package
    
  dangerous:
    - run_shell_command
    - delete_file
    - modify_config
\`\`\`

**Safety Gates:**
1. **Path Trust** - Verify file operations within trusted roots
2. **Tool Scope** - Check RBAC permissions before execution
3. **Consent Flow** - Prompt for dangerous operations
4. **Audit Trail** - Log all tool executions with context

### 6. Session & Checkpoint (`memory/session.py`)

**Session Memory:**
\`\`\`python
class Session:
    id: str
    created_at: datetime
    context: Dict[str, Any]  # Files, diffs, tools used
    history: List[Turn]       # Conversation turns
    checkpoints: List[CheckpointID]
\`\`\`

**Checkpoint Structure:**
\`\`\`json
{
  "id": "ckpt_abc123",
  "timestamp": "2025-01-14T10:30:00Z",
  "session_id": "sess_xyz789",
  "file_states": {
    "src/main.py": "sha256:...",
    "tests/test_main.py": "sha256:..."
  },
  "conversation_state": {
    "turns": 15,
    "last_intent": "code_edit",
    "active_plan": null
  },
  "metadata": {
    "description": "Before refactoring auth module",
    "tags": ["pre-refactor", "stable"]
  }
}
\`\`\`

**Commands:**
- `/checkpoint [description]` - Save current state
- `/restore <id>` - Restore to checkpoint
- `/checkpoints` - List all checkpoints
- `/diff <id>` - Show changes since checkpoint

### 7. Observability (`observability/otel.py`)

**Instrumentation Points:**
- Input parsing (latency, intent confidence)
- LLM calls (tokens, latency, provider, cost)
- Tool executions (duration, success/failure, output size)
- File operations (read/write counts, bytes)
- User interactions (accepts, rejects, cancellations)

**Trace Structure:**
\`\`\`
Span: user_input
  ├─ Span: parse_input
  ├─ Span: resolve_intent
  │   └─ Span: llm_call (provider=openai, model=gpt-4)
  ├─ Span: execute_plan
  │   ├─ Span: tool_call (tool=read_file)
  │   ├─ Span: tool_call (tool=write_file)
  │   └─ Span: checkpoint_save
  └─ Span: render_output
\`\`\`

**Metrics:**
- `superagent.input.latency` (histogram)
- `superagent.llm.tokens` (counter)
- `superagent.llm.cost` (counter)
- `superagent.tool.executions` (counter)
- `superagent.diff.accepts` (counter)
- `superagent.errors` (counter)

---

## User Flows

### Flow 1: Natural Language Task

**Input:** `make the auth module more secure`

\`\`\`
1. Parse input → Intent: Task (confidence: 0.85)
2. Show reasoning panel:
   ┌─ Understanding Request ─────────────────────┐
   │ Task: Improve security in auth module       │
   │ Scope: Authentication & authorization code  │
   │ Approach: Add input validation, rate        │
   │           limiting, and audit logging       │
   └─────────────────────────────────────────────┘

3. Generate plan:
   ┌─ Execution Plan ────────────────────────────┐
   │ 1. Analyze current auth implementation      │
   │ 2. Identify security vulnerabilities        │
   │ 3. Add input validation                     │
   │ 4. Implement rate limiting                  │
   │ 5. Add audit logging                        │
   │ 6. Update tests                             │
   └─────────────────────────────────────────────┘

4. Execute with tool calls:
   [✓] read_file(src/auth.py)
   [✓] analyze_security(src/auth.py)
   [⚠] write_file(src/auth.py) - Requires approval

5. Show diff preview:
   ┌─ Changes Preview ───────────────────────────┐
   │ src/auth.py: +45/-12 lines                  │
   │ tests/test_auth.py: +30/-5 lines            │
   │                                             │
   │ Risk: Medium | Impact: High                │
   │ Rollback: Available via /undo              │
   └─────────────────────────────────────────────┘

6. User accepts → Apply changes → Checkpoint
\`\`\`

### Flow 2: Diff-First Code Edit

**Input:** `@src/api.py add error handling to the upload endpoint`

\`\`\`
1. Load context: src/api.py (150 lines)
2. Identify target: upload_endpoint function
3. Generate changes (dry-run)
4. Show diff:
   ┌─ src/api.py ────────────────────────────────┐
   │ @@ -45,6 +45,12 @@                          │
   │  async def upload_endpoint(file: UploadFile)│
   │ +    try:                                    │
   │ +        if file.size > MAX_SIZE:           │
   │ +            raise ValueError("File too big")│
   │          data = await file.read()           │
   │          return process(data)               │
   │ +    except Exception as e:                 │
   │ +        logger.error(f"Upload failed: {e}")│
   │ +        raise HTTPException(500)           │
   └─────────────────────────────────────────────┘

5. Options: [A]ccept [R]eject [P]artial [E]dit
6. User: A → Apply → Checkpoint
\`\`\`

### Flow 3: Checkpoint & Restore

**Scenario:** Experiment with refactoring, then rollback

\`\`\`
1. User: /checkpoint "before refactoring"
   → Saved: ckpt_abc123

2. User: refactor the database layer to use async
   → Makes changes across 5 files

3. User: run tests
   → Tests fail

4. User: /restore ckpt_abc123
   → Restored 5 files to previous state
   → Session context preserved
\`\`\`

---

## Configuration

### settings.yaml

\`\`\`yaml
# SuperAgent UX Configuration

# Theme
theme:
  mode: auto  # light | dark | auto
  accent_color: "#007AFF"
  high_contrast: false

# Behavior
behavior:
  auto_accept_safe_tools: true
  show_reasoning: true
  show_token_usage: true
  confirm_dangerous_ops: true
  
# Performance
performance:
  max_context_tokens: 8000
  autocomplete_debounce_ms: 150
  spinner_delay_ms: 100
  
# Checkpointing
checkpointing:
  enabled: true
  auto_checkpoint_interval: 10  # turns
  max_checkpoints: 50
  
# Observability
observability:
  telemetry_enabled: true
  otel_endpoint: "http://localhost:4317"
  log_level: "INFO"
  redact_secrets: true
  
# Accessibility
accessibility:
  screen_reader_mode: false
  keyboard_shortcuts: true
  show_key_hints: true
\`\`\`

### policy.yaml

\`\`\`yaml
# RBAC & Security Policy

# Trusted paths (no confirmation needed)
trusted_paths:
  - "./src"
  - "./tests"
  - "./docs"

# Blocked paths (always deny)
blocked_paths:
  - "/etc"
  - "/usr"
  - "~/.ssh"
  - "~/.aws"

# Tool allowlist (auto-approve)
allowed_tools:
  - read_file
  - search_code
  - analyze_dependencies
  - run_tests
  - format_code

# Tool denylist (always block)
denied_tools:
  - delete_database
  - modify_system_config

# Roles
roles:
  default: developer
  
permissions:
  viewer:
    - read_files
    - ask_questions
    
  developer:
    - read_files
    - write_files
    - run_tests
    - use_safe_tools
    
  admin:
    - all_permissions
\`\`\`

---

## Acceptance Criteria

### Performance
- ✅ First token < 400ms (warm provider)
- ✅ UI responsive during tool I/O
- ✅ Autocomplete < 150ms latency
- ✅ Diff rendering < 100ms for files <1000 lines

### Safety
- ✅ Shell commands blocked without consent
- ✅ Path validation prevents escaping trusted roots
- ✅ Secrets redacted in logs and telemetry
- ✅ Audit trail for all tool executions

### Workflow
- ✅ Explain → Plan → Diff → Apply → Checkpoint works end-to-end
- ✅ Partial apply allows hunk selection
- ✅ Undo/restore works correctly
- ✅ Session persists across restarts

### Accessibility
- ✅ Screen reader mode narrates sections
- ✅ High contrast theme meets WCAG AA
- ✅ Keyboard shortcuts for all actions
- ✅ Key hints visible and accurate

### Reliability
- ✅ Provider fallback maintains session state
- ✅ Graceful degradation on network issues
- ✅ Atomic file operations (no partial writes)
- ✅ Checkpoint integrity verified on restore

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- UX Orchestrator with state machine
- Intent Router with NL parsing
- Basic rendering components
- Configuration system

### Phase 2: Diff Engine (Week 2)
- Dry-run execution
- Diff generation and display
- Partial apply with hunk selection
- Atomic file operations

### Phase 3: Safety & RBAC (Week 3)
- Permission system
- Tool scopes and gates
- Path trust validation
- Audit logging

### Phase 4: Session & Checkpoint (Week 4)
- Session persistence
- Checkpoint save/restore
- State journaling
- Integrity verification

### Phase 5: Observability (Week 5)
- OpenTelemetry integration
- Metrics and traces
- Grafana dashboards
- Performance profiling

### Phase 6: Polish & Testing (Week 6)
- Theme refinement
- Accessibility features
- Comprehensive tests
- Documentation

---

## Appendix

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit SuperAgent |
| `Ctrl+L` | Clear screen |
| `Ctrl+R` | Search history |
| `Tab` | Autocomplete |
| `↑/↓` | Navigate history |
| `Ctrl+P/N` | Previous/Next suggestion |
| `/` | Command mode |
| `@` | File include |

### Command Reference

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/theme <mode>` | Change theme |
| `/checkpoint [desc]` | Save checkpoint |
| `/restore <id>` | Restore checkpoint |
| `/checkpoints` | List checkpoints |
| `/diff <id>` | Show diff since checkpoint |
| `/undo` | Undo last change |
| `/tools` | List available tools |
| `/settings` | Open settings |
| `/clear` | Clear screen |
| `/exit` | Exit SuperAgent |

### Error Handling

**Graceful Degradation:**
- Provider timeout → Fallback provider
- Network error → Retry with exponential backoff
- Parse error → Request clarification
- Tool failure → Show error, continue session

**User Feedback:**
- Errors shown in dedicated panel
- Suggested fixes when available
- Rollback option always present
- Support contact info in critical errors

---

**End of Specification**

**Next Steps:**
1. Implement UX Orchestrator
2. Build rendering components
3. Create Intent Router
4. Add Diff Engine
5. Integrate RBAC
6. Add observability
7. Write comprehensive tests
8. Update documentation
