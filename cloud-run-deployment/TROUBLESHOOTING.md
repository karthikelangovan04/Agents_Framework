# Troubleshooting Guide

> **⚠️ Important**: Before troubleshooting, check [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for current known bugs and limitations.

## Common Issues and Solutions

### 1. 403 Forbidden Error

**Symptom:**
```
Error: 403 Forbidden when ADK agent tries to call MCP server
```

**Causes:**
- IAM permissions not configured
- Service account doesn't have `roles/run.invoker`
- MCP server URL incorrect

**Solution:**
```bash
# Re-run IAM setup
cd scripts
./setup-iam.sh

# Verify permissions
gcloud run services get-iam-policy mcp-server \
  --region ${GOOGLE_CLOUD_REGION}

# Check service account
echo "${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
```

### 2. Authentication Token Not Obtained

**Symptom:**
```
Failed to get ID token: ...
```

**Causes:**
- Application Default Credentials not set
- Service account lacks necessary permissions
- Running locally without proper setup

**Solution:**
```bash
# Set up ADC
gcloud auth application-default login

# Verify ADC works
gcloud auth application-default print-access-token

# For Cloud Run, verify service account has necessary roles
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com"
```

### 3. LLM API Errors

**Symptom:**
```
Error calling Vertex AI API
Permission denied
```

**Causes:**
- Vertex AI API not enabled
- Service account lacks Vertex AI User role
- Wrong project/location configured

**Solution:**
```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Verify environment variables
gcloud run services describe adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --format="value(spec.template.spec.containers[0].env)"
```

### 4. MCP Tool Not Found

**Symptom:**
```
Tool 'get_exchange_rate' not found
MCP connection failed
```

**Causes:**
- MCP_SERVER_URL incorrect (missing `/sse` path)
- MCP server not running
- Network connectivity issues

**Solution:**
```bash
# Verify MCP server URL format
echo ${MCP_SERVER_URL}
# Should be: https://mcp-server-xxx-uc.a.run.app/sse

# Check MCP server is running
gcloud run services describe mcp-server \
  --region ${GOOGLE_CLOUD_REGION}

# Test MCP server directly (with auth)
ID_TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer ${ID_TOKEN}" \
  ${MCP_SERVER_URL}/health
```

### 5. Container Build Failures

**Symptom:**
```
Error building container image
```

**Causes:**
- Dockerfile syntax errors
- Missing dependencies
- Cloud Build API not enabled

**Solution:**
```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Test build locally (if Docker installed)
cd mcp-server
docker build -t test-mcp-server .

# Check Cloud Build logs
gcloud builds list --limit 5
```

### 6. Environment Variables Not Set

**Symptom:**
```
MCP_SERVER_URL not found
GOOGLE_CLOUD_PROJECT not set
```

**Solution:**
```bash
# Update environment variables
gcloud run services update adk-agent \
  --update-env-vars "MCP_SERVER_URL=https://mcp-server-xxx.run.app/sse,GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --region ${GOOGLE_CLOUD_REGION}

# Verify
gcloud run services describe adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --format="value(spec.template.spec.containers[0].env)"
```

### 7. Service Not Found

**Symptom:**
```
Service 'mcp-server' not found
```

**Solution:**
```bash
# List all services
gcloud run services list --region ${GOOGLE_CLOUD_REGION}

# Check if service exists in different region
gcloud run services list --platform managed

# Redeploy if needed
cd scripts
./deploy-mcp-server.sh
```

### 8. High Latency or Timeouts

**Symptom:**
```
Request timeout
Slow response times
```

**Solution:**
```bash
# Increase timeout
gcloud run services update adk-agent \
  --timeout 600 \
  --region ${GOOGLE_CLOUD_REGION}

# Increase memory/CPU
gcloud run services update adk-agent \
  --memory 2Gi \
  --cpu 4 \
  --region ${GOOGLE_CLOUD_REGION}

# Check logs for bottlenecks
gcloud run services logs read adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --limit 100
```

### 9. ID Token Expiration

**Symptom:**
```
Token expired
Authentication fails after some time
```

**Note:** ID tokens expire after ~1 hour. The `auth_helper.py` gets a fresh token each time, but if you're caching tokens, you need to refresh them.

**Solution:**
- The current implementation gets fresh tokens on each request
- If implementing caching, check token expiration:
  ```python
  import jwt
  decoded = jwt.decode(token, options={"verify_signature": False})
  exp_time = decoded.get('exp')
  ```

### 10. Local Testing Issues

**Symptom:**
```
Works in Cloud Run but not locally
```

**Solution:**
```bash
# Set up ADC for local testing
gcloud auth application-default login

# Set environment variables
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export MCP_SERVER_URL="http://localhost:8080/sse"  # For local MCP server
# OR use Cloud Run proxy:
# gcloud run services proxy mcp-server --region ${REGION}
# export MCP_SERVER_URL="http://127.0.0.1:8080/sse"

# Run locally
cd adk-agent
python main.py
```

## Debugging Commands

### Check Service Status
```bash
# List all services
gcloud run services list --region ${GOOGLE_CLOUD_REGION}

# Get service details
gcloud run services describe adk-agent --region ${GOOGLE_CLOUD_REGION}
```

### View Logs
```bash
# Real-time logs
gcloud run services logs tail adk-agent --region ${GOOGLE_CLOUD_REGION}

# Last 50 log entries
gcloud run services logs read adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --limit 50
```

### Test Authentication
```bash
# Get ID token
gcloud auth print-identity-token

# Test MCP server with token
ID_TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer ${ID_TOKEN}" \
  https://mcp-server-xxx.run.app/health
```

### Check IAM Permissions
```bash
# MCP server IAM policy
gcloud run services get-iam-policy mcp-server \
  --region ${GOOGLE_CLOUD_REGION}

# Project-level IAM
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com"
```

### Verify Environment Variables
```bash
# Get all env vars
gcloud run services describe adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --format="value(spec.template.spec.containers[0].env)"

# Update env vars
gcloud run services update adk-agent \
  --update-env-vars "KEY=value" \
  --region ${GOOGLE_CLOUD_REGION}
```

## Getting Help

1. **Check Logs**: Always start with service logs
2. **Verify Configuration**: Double-check environment variables and IAM
3. **Test Components**: Test MCP server and agent separately
4. **Review Documentation**: Check README.md for detailed steps
5. **Google Cloud Support**: Use Cloud Console support for billing/account issues

## Prevention Tips

1. **Always run setup-iam.sh** after deploying MCP server
2. **Verify environment variables** before deploying agent
3. **Test locally first** when possible
4. **Monitor logs** during initial deployment
5. **Use test-deployment.sh** to verify everything works
