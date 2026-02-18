# Changelog

## 2026-02-17 - Deployment Script Updates and Issue Documentation

### Added
- **KNOWN_ISSUES.md** - Comprehensive document detailing the MCP connection async context error
  - Root cause analysis
  - Attempted fixes
  - Current status
  - Potential solutions

### Updated
- **scripts/deploy-adk-agent.sh**
  - Enhanced error messages and documentation
  - Improved service account detection logic
  - Added Python 3.12 verification check
  - Added reference to KNOWN_ISSUES.md in output
  - Better next steps guidance

- **adk-agent/Dockerfile**
  - Updated comments to reflect Python 3.12 usage
  - Added explanation for Python version choice

- **INDEX.md**
  - Added KNOWN_ISSUES.md to documentation index
  - Updated troubleshooting section to reference known issues

- **TROUBLESHOOTING.md**
  - Added reference to KNOWN_ISSUES.md at the top

- **README.md**
  - Added reference to KNOWN_ISSUES.md in troubleshooting section
  - Added specific entry for MCP connection async context error

### Fixed
- **adk-agent/agent.py**
  - Changed from static headers to `header_provider` callback for dynamic authentication
  - Headers now generated when MCP connection is established (not at module load time)
  - Added error handling for authentication failures

- **adk-agent/main.py**
  - Fixed `Runner` initialization (added `app_name` parameter)
  - Added session creation if session doesn't exist
  - Improved error handling and logging
  - Added health endpoint with Python version info

### Technical Details

#### Python Version Upgrade
- Upgraded from Python 3.11 to Python 3.12
- Python 3.12 has improved task context management
- Helps with async context handling (though issue persists)

#### Authentication Improvements
- Changed from static header generation to dynamic `header_provider`
- Headers generated when connection is established, not at import time
- Ensures Cloud Run credentials are available when needed

#### Known Issue
- MCP connection fails with async context error
- Root cause: AnyIO TaskGroup/CancelScope incompatibility with Cloud Run
- Status: Documented in KNOWN_ISSUES.md
- Workaround: None currently available

### Files Modified
- `scripts/deploy-adk-agent.sh`
- `adk-agent/Dockerfile`
- `adk-agent/agent.py`
- `adk-agent/main.py`
- `INDEX.md`
- `TROUBLESHOOTING.md`
- `README.md`

### Files Created
- `KNOWN_ISSUES.md`
- `CHANGELOG.md` (this file)

### Next Steps
1. Report MCP async context issue to ADK team
2. Test SSE connection as alternative to StreamableHTTP
3. Monitor ADK library updates for fixes
4. Consider local MCP server connection if available

---

**Note**: All deployment infrastructure is correct and working. The only remaining issue is the MCP client library's async context management in Cloud Run environment.
