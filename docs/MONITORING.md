# Monitoring and Security

Comprehensive monitoring, analytics, and security systems for SuperAgent.

## Monitoring

### Metrics Collection

Track performance metrics with counters, gauges, histograms, and timers:

\`\`\`python
from superagent.monitoring import MetricsCollector, Timer

collector = MetricsCollector()

# Increment counter
collector.increment("api_calls")

# Set gauge
collector.set_gauge("active_connections", 42)

# Record histogram
collector.record_histogram("response_time", 0.5)

# Time operations
with Timer(collector, "llm_call"):
    # Your code here
    pass

# Get statistics
stats = collector.get_histogram_stats("response_time")
print(f"P95 latency: {stats['p95']:.3f}s")
\`\`\`

### Telemetry

Track events and user actions:

\`\`\`python
from superagent.monitoring import TelemetryManager

telemetry = TelemetryManager()
telemetry.set_user_id("user123")

# Track custom events
telemetry.track_event("feature_used", properties={"feature": "chat"})

# Track LLM calls
telemetry.track_llm_call("openai", "gpt-4", tokens=1000, duration=1.5, success=True)

# Track tool executions
telemetry.track_tool_execution("web_search", duration=2.0, success=True)

# Query events
events = telemetry.get_events(event_type="llm_call", limit=10)
\`\`\`

### Health Checks

Monitor system health:

\`\`\`python
from superagent.monitoring import HealthChecker

checker = HealthChecker()

# Check individual components
check = await checker.check_llm_provider("openai", provider)

# Check all components
results = await checker.check_all({
    "llm": llm_provider,
    "memory": memory_manager,
    "tools": tool_registry,
})

# Get overall status
status = checker.get_overall_status()
print(f"System status: {status}")
\`\`\`

### Analytics

Track usage and costs:

\`\`\`python
from superagent.monitoring import AnalyticsTracker

tracker = AnalyticsTracker()

# Track requests
tracker.track_request(
    provider="openai",
    model="gpt-4",
    tokens=1000,
    latency=1.5,
    success=True,
    tool_calls=["search", "calculate"]
)

# Get usage statistics
stats = tracker.get_usage_stats()
print(f"Total cost: ${stats.total_cost:.2f}")
print(f"Total tokens: {stats.total_tokens}")

# Get cost breakdown
breakdown = tracker.get_cost_breakdown()
for model, cost in breakdown.items():
    print(f"{model}: ${cost:.2f}")

# Get top models and tools
top_models = tracker.get_top_models(limit=5)
top_tools = tracker.get_top_tools(limit=5)
\`\`\`

## Security

### Role-Based Access Control (RBAC)

Manage permissions with roles:

\`\`\`python
from superagent.security import RBACManager, Permission

rbac = RBACManager()

# Assign role to user
rbac.assign_role("user123", "user")

# Check permissions
if rbac.has_permission("user123", Permission.TOOL_EXECUTE):
    # Execute tool
    pass

# Get user permissions
permissions = rbac.get_user_permissions("user123")

# Create custom role
from superagent.security import Role

custom_role = Role(
    name="analyst",
    permissions={Permission.LLM_READ, Permission.MEMORY_READ},
    description="Read-only analyst access"
)
rbac.create_role(custom_role)
\`\`\`

### Audit Logging

Track security events:

\`\`\`python
from superagent.security import AuditLogger

audit = AuditLogger()

# Log authentication
audit.log_authentication("user123", success=True, ip_address="192.168.1.1")

# Log authorization
audit.log_authorization("user123", "llm:read", "gpt-4", granted=True)

# Log data access
audit.log_data_access("user123", "memory", "read")

# Log configuration changes
audit.log_configuration_change("admin", "max_tokens", 1000, 2000)

# Query audit events
events = audit.get_events(
    user_id="user123",
    event_type="authentication",
    limit=10
)
\`\`\`

### Secrets Management

Securely store and rotate secrets:

\`\`\`python
from superagent.security import SecretsManager

secrets = SecretsManager()

# Store secret
secrets.set_secret("openai_api_key", "sk-...")

# Retrieve secret
api_key = secrets.get_secret("openai_api_key")

# Rotate secret
secrets.rotate_secret("openai_api_key", "sk-new...")

# Check if rotation needed
if secrets.needs_rotation("openai_api_key", max_age_days=90):
    # Rotate the secret
    pass

# List secrets (names only)
secret_names = secrets.list_secrets()
\`\`\`

## Best Practices

1. **Always use metrics** - Track all important operations
2. **Enable telemetry** - Understand usage patterns
3. **Monitor health** - Set up regular health checks
4. **Track costs** - Monitor LLM usage and costs
5. **Use RBAC** - Implement proper access control
6. **Audit everything** - Log all security-relevant events
7. **Rotate secrets** - Regularly rotate API keys and credentials
8. **Review logs** - Regularly review audit logs for anomalies
