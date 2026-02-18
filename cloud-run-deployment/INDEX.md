# Cloud Run Deployment - Index

## 📚 Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| **[README.md](README.md)** | Comprehensive deployment guide | Start here for detailed step-by-step instructions |
| **[QUICK_START.md](QUICK_START.md)** | Quick reference guide | For experienced users who need a quick reminder |
| **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** | Architecture and overview | Understanding the system design |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and solutions | When something goes wrong |
| **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** | Known issues and limitations | Current bugs and workarounds |
| **[INDEX.md](INDEX.md)** | This file - navigation guide | Finding what you need |

## 🚀 Quick Navigation

### First Time Deployment
1. Read [README.md](README.md) - Full deployment guide
2. Follow Step 1-7 in README.md
3. Use [QUICK_START.md](QUICK_START.md) as a checklist

### Quick Deployment
1. Use [QUICK_START.md](QUICK_START.md)
2. Run scripts in `scripts/` directory
3. Test with `scripts/test-deployment.sh`

### Understanding Architecture
1. Read [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
2. Review code in `mcp-server/` and `adk-agent/`
3. Check authentication flow in `adk-agent/auth_helper.py`

### Troubleshooting
1. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - Current known bugs
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
3. Review service logs
4. Verify IAM permissions

## 📁 Directory Structure

```
cloud-run-deployment/
│
├── 📄 Documentation
│   ├── README.md              # Main deployment guide
│   ├── QUICK_START.md         # Quick reference
│   ├── DEPLOYMENT_SUMMARY.md  # Architecture overview
│   ├── TROUBLESHOOTING.md     # Common issues
│   ├── KNOWN_ISSUES.md        # Known bugs and limitations
│   └── INDEX.md               # This file
│
├── 🔧 MCP Server
│   └── mcp-server/
│       ├── server.py          # FastMCP server code
│       ├── requirements.txt   # Dependencies
│       ├── Dockerfile         # Container definition
│       └── .env.example        # Environment template
│
├── 🤖 ADK Agent
│   └── adk-agent/
│       ├── agent.py           # ADK agent definition
│       ├── main.py            # FastAPI application
│       ├── auth_helper.py     # Authentication helper
│       ├── requirements.txt   # Dependencies
│       ├── Dockerfile         # Container definition
│       └── .env.example       # Environment template
│
└── 📜 Scripts
    └── scripts/
        ├── deploy-mcp-server.sh    # Deploy MCP server
        ├── deploy-adk-agent.sh     # Deploy ADK agent
        ├── setup-iam.sh            # Configure IAM
        └── test-deployment.sh      # Test services
```

## 🎯 Common Tasks

### Deploy Everything
```bash
cd scripts
./deploy-mcp-server.sh
export MCP_SERVER_URL="https://mcp-server-xxx.run.app/sse"
./setup-iam.sh
./deploy-adk-agent.sh
```

### Test Deployment
```bash
cd scripts
./test-deployment.sh
```

### View Logs
```bash
# ADK Agent
gcloud run services logs read adk-agent --region ${REGION}

# MCP Server
gcloud run services logs read mcp-server --region ${REGION}
```

### Update Configuration
```bash
# Update environment variables
gcloud run services update adk-agent \
  --update-env-vars "KEY=value" \
  --region ${REGION}
```

## 🔑 Key Concepts

### Service-to-Service Authentication
- **MCP Server**: Private (requires authentication)
- **ADK Agent**: Gets ID token → Includes in request → Cloud Run validates
- **IAM**: Agent service account needs `roles/run.invoker` on MCP server

### LLM Authentication
- **Vertex AI**: Uses Application Default Credentials (recommended)
- **Google AI Studio**: Uses API key (for development)

### Deployment Flow
1. Deploy MCP Server (private)
2. Configure IAM permissions
3. Deploy ADK Agent (with MCP server URL)
4. Test end-to-end

## 📖 Reading Order

### For First-Time Users
1. [README.md](README.md) - Complete guide
2. [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Understand architecture
3. [QUICK_START.md](QUICK_START.md) - Quick reference

### For Troubleshooting
1. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - Current known bugs
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
3. Service logs - Actual errors
4. [README.md](README.md) - Detailed steps

### For Understanding
1. [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Overview
2. Code files - Implementation details
3. [README.md](README.md) - Configuration

## 🔗 External Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Service-to-Service Auth](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [ADK Documentation](https://google.github.io/adk-docs)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Vertex AI](https://cloud.google.com/vertex-ai)

## 💡 Tips

1. **Always check logs first** when debugging
2. **Verify IAM permissions** if getting 403 errors
3. **Test locally** before deploying to Cloud Run
4. **Use test-deployment.sh** to verify everything works
5. **Keep MCP_SERVER_URL updated** after MCP server deployment

## 📞 Getting Help

1. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for current bugs
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
3. Review service logs
4. Verify configuration
5. Consult [README.md](README.md) for detailed steps
