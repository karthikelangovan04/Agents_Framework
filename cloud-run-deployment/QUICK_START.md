# Quick Start Guide

## Prerequisites Checklist

- [ ] Google Cloud Project with billing enabled
- [ ] gcloud CLI installed (`gcloud --version`)
- [ ] Authenticated (`gcloud auth login`)
- [ ] Project set (`gcloud config set project YOUR_PROJECT_ID`)

## One-Command Setup

```bash
# Set your project
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

# Enable APIs
gcloud services enable \
  cloudrun.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  --project ${GOOGLE_CLOUD_PROJECT}

# Set up authentication
gcloud auth application-default login
```

## Deployment Steps

### 1. Deploy MCP Server

```bash
cd cloud-run-deployment/scripts
./deploy-mcp-server.sh

# Save the MCP server URL from output
export MCP_SERVER_URL="https://mcp-server-xxx-uc.a.run.app/sse"
```

### 2. Set Up Authentication

```bash
./setup-iam.sh
```

### 3. Deploy ADK Agent

```bash
./deploy-adk-agent.sh
```

### 4. Test

```bash
# Get agent URL
AGENT_URL=$(gcloud run services describe adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --format 'value(status.url)')

# Test the agent
curl -X POST ${AGENT_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 100 USD in EUR?"}'
```

## Common Commands

### View Logs

```bash
# ADK Agent logs
gcloud run services logs read adk-agent --region ${GOOGLE_CLOUD_REGION} --limit 50

# MCP Server logs
gcloud run services logs read mcp-server --region ${GOOGLE_CLOUD_REGION} --limit 50
```

### Check Service Status

```bash
gcloud run services list --region ${GOOGLE_CLOUD_REGION}
```

### Update Environment Variables

```bash
gcloud run services update adk-agent \
  --update-env-vars "MCP_SERVER_URL=new-url" \
  --region ${GOOGLE_CLOUD_REGION}
```

## Troubleshooting Quick Fixes

**403 Forbidden:**
```bash
# Re-run IAM setup
./setup-iam.sh
```

**Authentication errors:**
```bash
# Verify ADC
gcloud auth application-default print-access-token
```

**Service not found:**
```bash
# List all services
gcloud run services list --region ${GOOGLE_CLOUD_REGION}
```
