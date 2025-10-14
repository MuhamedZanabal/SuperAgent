# SuperAgent Deployment Guide

## Overview

This guide covers deploying SuperAgent in various environments from local development to production Kubernetes clusters.

## Prerequisites

- Python 3.12+
- Docker (for containerized deployment)
- Kubernetes cluster (for K8s deployment)
- API keys for LLM providers

## Local Development

### Installation

\`\`\`bash
# Clone repository
git clone https://github.com/your-org/superagent.git
cd superagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e '.[dev]'

# Initialize configuration
superagent init
\`\`\`

### Configuration

Create `.env` file:

\`\`\`env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SUPERAGENT_DEFAULT_MODEL=gpt-4
SUPERAGENT_TEMPERATURE=0.7
\`\`\`

### Running

\`\`\`bash
# Interactive shell
superagent

# One-shot execution
superagent run "Analyze this data"

# With specific model
superagent --model gpt-4 run "Complex task"
\`\`\`

## Docker Deployment

### Build Image

\`\`\`bash
docker build -t superagent:latest .
\`\`\`

### Run Container

\`\`\`bash
docker run -it \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/data:/data \
  superagent:latest
\`\`\`

### Docker Compose

\`\`\`bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f superagent

# Stop services
docker-compose down
\`\`\`

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm (optional)

### Create Secrets

\`\`\`bash
kubectl create secret generic superagent-secrets \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY
\`\`\`

### Deploy

\`\`\`bash
# Apply manifests
kubectl apply -f kubernetes/

# Check status
kubectl get pods -l app=superagent

# View logs
kubectl logs -l app=superagent -f
\`\`\`

### Scaling

\`\`\`bash
# Scale replicas
kubectl scale deployment superagent --replicas=5

# Autoscaling
kubectl autoscale deployment superagent \
  --min=3 --max=10 --cpu-percent=70
\`\`\`

## Production Considerations

### Security

1. **API Key Management**
   - Use secrets management (Vault, AWS Secrets Manager)
   - Rotate keys regularly
   - Never commit keys to version control

2. **Network Security**
   - Use TLS for all connections
   - Implement network policies
   - Restrict egress traffic

3. **Access Control**
   - Enable RBAC
   - Use service accounts
   - Audit all access

### Monitoring

1. **Metrics**
   - Prometheus for metrics collection
   - Grafana for visualization
   - Alert on critical metrics

2. **Logging**
   - Centralized logging (ELK, Loki)
   - Structured JSON logs
   - Log retention policies

3. **Tracing**
   - OpenTelemetry integration
   - Distributed tracing
   - Performance profiling

### High Availability

1. **Redundancy**
   - Multiple replicas
   - Multi-zone deployment
   - Load balancing

2. **Backup**
   - Regular data backups
   - Disaster recovery plan
   - Test restore procedures

3. **Health Checks**
   - Liveness probes
   - Readiness probes
   - Startup probes

## Environment-Specific Configurations

### Development

\`\`\`yaml
# config.dev.yaml
environment: development
debug: true
log_level: DEBUG
sandbox_enabled: false
\`\`\`

### Staging

\`\`\`yaml
# config.staging.yaml
environment: staging
debug: false
log_level: INFO
sandbox_enabled: true
rate_limit: 100
\`\`\`

### Production

\`\`\`yaml
# config.prod.yaml
environment: production
debug: false
log_level: WARNING
sandbox_enabled: true
rate_limit: 1000
encryption_enabled: true
\`\`\`

## Troubleshooting

### Common Issues

1. **API Key Errors**
   \`\`\`bash
   # Verify keys are set
   superagent config show
   
   # Test provider connection
   superagent providers
   \`\`\`

2. **Memory Issues**
   \`\`\`bash
   # Check memory usage
   kubectl top pods
   
   # Increase memory limits
   kubectl set resources deployment superagent \
     --limits=memory=4Gi
   \`\`\`

3. **Performance Issues**
   \`\`\`bash
   # Enable profiling
   superagent --profile run "task"
   
   # Check metrics
   curl http://localhost:9090/metrics
   \`\`\`

### Logs

\`\`\`bash
# View application logs
kubectl logs -l app=superagent --tail=100

# Follow logs
kubectl logs -l app=superagent -f

# Filter by level
kubectl logs -l app=superagent | grep ERROR
\`\`\`

## Maintenance

### Updates

\`\`\`bash
# Pull latest image
docker pull superagent:latest

# Rolling update
kubectl set image deployment/superagent \
  superagent=superagent:latest

# Rollback if needed
kubectl rollout undo deployment/superagent
\`\`\`

### Backup

\`\`\`bash
# Backup data directory
kubectl exec -it superagent-pod -- \
  tar czf /tmp/backup.tar.gz /data

# Copy backup
kubectl cp superagent-pod:/tmp/backup.tar.gz \
  ./backup-$(date +%Y%m%d).tar.gz
\`\`\`

### Monitoring

\`\`\`bash
# Check health
curl http://localhost:8000/health

# View metrics
curl http://localhost:9090/metrics

# Check resource usage
kubectl top pods -l app=superagent
\`\`\`

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/superagent/issues
- Documentation: https://docs.superagent.dev
- Community: https://discord.gg/superagent
