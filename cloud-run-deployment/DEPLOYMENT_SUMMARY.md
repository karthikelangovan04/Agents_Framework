# Deployment Summary

## Overview

This deployment package provides a complete solution for deploying an MCP server and ADK agent as separate Cloud Run services with secure service-to-service authentication.

## Key Components

### 1. MCP Server (`mcp-server/`)
- **Purpose**: Exposes currency exchange rate tools via FastMCP
- **Deployment**: Private Cloud Run service (authentication required)
- **Technology**: FastMCP, Python 3.11
- **Endpoints**: `/sse` (MCP SSE protocol endpoint)

### 2. ADK Agent (`adk-agent/`)
- **Purpose**: AI agent that uses MCP tools for currency conversions
- **Deployment**: Public Cloud Run service (can be made private)
- **Technology**: Google ADK, FastAPI, Python 3.11
- **Endpoints**: `/chat`, `/health`, `/`

### 3. Authentication (`adk-agent/auth_helper.py`)
- **Purpose**: Handles service-to-service authentication
- **Method**: ID tokens via Google Auth Library
- **Flow**: Gets ID token → Includes in Authorization header → Cloud Run validates

## Architecture Flow

```
User Request
    ↓
ADK Agent (Cloud Run)
    ↓ [Gets ID Token]
    ↓ [Authorization: Bearer <token>]
MCP Server (Cloud Run - Private)
    ↓ [Validates Token]
    ↓ [Checks IAM]
    ↓ [Processes Request]
External API (Frankfurter)
    ↓
Response flows back
```

## Authentication Details

### Service-to-Service Authentication

1. **MCP Server** is deployed with `--no-allow-unauthenticated`
2. **ADK Agent** uses its service account identity
3. **auth_helper.py** gets ID token:
   ```python
   token = id_token.fetch_id_token(request, audience=mcp_server_url)
   ```
4. Token is included in request headers
5. Cloud Run validates token and checks IAM permissions
6. Request proceeds if authorized

### LLM Authentication

**Option 1: Vertex AI (Recommended)**
- Uses Application Default Credentials (ADC)
- Automatically available in Cloud Run
- Set `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
- Requires Vertex AI API enabled

**Option 2: Google AI Studio**
- Requires API key
- Set `GOOGLE_GENAI_USE_VERTEXAI=FALSE`
- Set `GOOGLE_API_KEY=your-key`
- Less secure for production

## File Structure

```
cloud-run-deployment/
├── README.md                    # Comprehensive deployment guide
├── QUICK_START.md               # Quick reference
├── DEPLOYMENT_SUMMARY.md        # This file
├── .gitignore                   # Git ignore rules
│
├── mcp-server/                  # MCP Server
│   ├── server.py                # FastMCP server code
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container definition
│   ├── .dockerignore            # Docker ignore rules
│   └── .env.example             # Environment template
│
├── adk-agent/                   # ADK Agent
│   ├── agent.py                 # ADK agent definition
│   ├── main.py                  # FastAPI application
│   ├── auth_helper.py           # Authentication helper
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container definition
│   ├── .dockerignore            # Docker ignore rules
│   └── .env.example             # Environment template
│
└── scripts/                     # Deployment scripts
    ├── deploy-mcp-server.sh     # Deploy MCP server
    ├── deploy-adk-agent.sh      # Deploy ADK agent
    ├── setup-iam.sh             # Configure IAM permissions
    └── test-deployment.sh       # Test deployed services
```

## Deployment Steps Summary

1. **Setup**: Enable APIs, authenticate, set project
2. **Deploy MCP Server**: Build and deploy as private service
3. **Configure IAM**: Grant agent permission to invoke MCP server
4. **Deploy ADK Agent**: Build and deploy with MCP server URL
5. **Test**: Verify both services work together

## Environment Variables

### MCP Server
- `PORT`: Set automatically by Cloud Run (default: 8080)

### ADK Agent
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `GOOGLE_CLOUD_LOCATION`: Region (e.g., us-central1)
- `GOOGLE_GENAI_USE_VERTEXAI`: TRUE for Vertex AI, FALSE for API key
- `GOOGLE_API_KEY`: Required if using Google AI Studio
- `GOOGLE_MODEL`: Model name (e.g., gemini-2.5-flash)
- `MCP_SERVER_URL`: Full URL to MCP server endpoint
- `PORT`: Set automatically by Cloud Run

## Security Considerations

1. **MCP Server**: Private (authentication required)
2. **IAM**: Least privilege (only `roles/run.invoker`)
3. **Secrets**: Use Secret Manager for sensitive data
4. **Monitoring**: Enable Cloud Logging
5. **Audit**: Review Cloud Audit Logs

## Cost Optimization

- **Memory**: MCP server (512Mi), Agent (1Gi)
- **CPU**: MCP server (1), Agent (2)
- **Instances**: Set max-instances based on expected load
- **Timeout**: 300 seconds (adjust as needed)

## Monitoring

### View Logs
```bash
# ADK Agent
gcloud run services logs read adk-agent --region ${REGION}

# MCP Server
gcloud run services logs read mcp-server --region ${REGION}
```

### Check Service Status
```bash
gcloud run services list --region ${REGION}
```

### Monitor Metrics
- Use Cloud Console → Cloud Run → Metrics
- Set up alerts for errors, latency, etc.

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check IAM permissions (`setup-iam.sh`)
2. **Authentication errors**: Verify ADC (`gcloud auth application-default login`)
3. **LLM errors**: Check Vertex AI API enabled and service account permissions
4. **MCP tool not found**: Verify MCP_SERVER_URL includes `/sse` path

### Debug Commands

```bash
# Check IAM policy
gcloud run services get-iam-policy mcp-server --region ${REGION}

# Test authentication
gcloud auth print-identity-token

# View service details
gcloud run services describe adk-agent --region ${REGION}
```

## Next Steps

1. **Customize**: Modify MCP server tools for your use case
2. **Scale**: Adjust memory/CPU based on load
3. **Secure**: Use Secret Manager for API keys
4. **Monitor**: Set up alerts and dashboards
5. **Optimize**: Review costs and performance

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Service-to-Service Auth](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [ADK Documentation](https://google.github.io/adk-docs)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Vertex AI](https://cloud.google.com/vertex-ai)
