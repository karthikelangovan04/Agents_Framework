# ADK Docs Extraction Guide

How the raw documentation was extracted from Google's ADK docs, and how to fetch everything from the repo root.

---

## 1. How the Raw Documents Were Extracted

### URL Mapping

The Google ADK docs are served at `https://google.github.io/adk-docs/` but the source lives in the [google/adk-docs](https://github.com/google/adk-docs) GitHub repo. Each web page maps to a raw markdown file.

**Pattern:**
```
https://google.github.io/adk-docs/<path>/
    ↓
https://raw.githubusercontent.com/google/adk-docs/main/docs/<path>.md
```

For section index pages, the file is usually `index.md`:
```
https://google.github.io/adk-docs/callbacks/
    → https://raw.githubusercontent.com/google/adk-docs/main/docs/callbacks/index.md
```

### Files Extracted for Callbacks/Plugins/Safety

| Web URL | Raw Markdown URL |
|---------|------------------|
| `adk-docs/safety/` | `raw.../docs/safety/index.md` |
| `adk-docs/callbacks/` | `raw.../docs/callbacks/index.md` |
| `adk-docs/callbacks/types-of-callbacks/` | `raw.../docs/callbacks/types-of-callbacks.md` |
| `adk-docs/callbacks/design-patterns-and-best-practices/` | `raw.../docs/callbacks/design-patterns-and-best-practices.md` |
| `adk-docs/plugins/` | `raw.../docs/plugins/index.md` |

### Extraction Method (curl)

```bash
curl -sL "https://raw.githubusercontent.com/google/adk-docs/main/docs/callbacks/index.md" -o "docs/callbacks/index.md"
```

- `-s` = silent
- `-L` = follow redirects
- `-o` = output file

---

## 2. How to Get Everything from Root

To fetch **all** docs from the repo, you have two main approaches.

### Option A: Clone the Repo

Clone the full repo and copy only `docs/`:

```bash
git clone --depth 1 https://github.com/google/adk-docs.git /tmp/adk-docs
cp -r /tmp/adk-docs/docs ./docs-full
rm -rf /tmp/adk-docs
```

You get the entire `docs/` tree (agents, callbacks, plugins, safety, deploy, etc.).

### Option B: Use GitHub API to List and Download

1. **List all files in `docs/` recursively:**

   ```bash
   curl -sL "https://api.github.com/repos/google/adk-docs/git/trees/main?recursive=1" \
     | python3 -c "
   import sys, json
   data = json.load(sys.stdin)
   for f in data.get('tree', []):
       if f['path'].startswith('docs/') and f['path'].endswith('.md'):
           print(f['path'])
   "
   ```

2. **Download each `.md` file:**

   ```bash
   BASE="https://raw.githubusercontent.com/google/adk-docs/main"
   # After getting the list above, for each path:
   curl -sL "$BASE/docs/callbacks/index.md" -o "docs/callbacks/index.md"
   # ... repeat for each path
   ```

### Option C: Script to Fetch All Docs

```bash
#!/bin/bash
# fetch-all-adk-docs.sh
BASE="https://raw.githubusercontent.com/google/adk-docs/main"
REPO="https://api.github.com/repos/google/adk-docs/git/trees/main?recursive=1"

mkdir -p docs
curl -sL "$REPO" | python3 -c "
import sys, json, os, urllib.request

data = json.load(sys.stdin)
base = 'https://raw.githubusercontent.com/google/adk-docs/main'
for f in data.get('tree', []):
    path = f['path']
    if path.startswith('docs/') and path.endswith('.md'):
        out = path
        os.makedirs(os.path.dirname(out), exist_ok=True)
        url = f'{base}/{path}'
        urllib.request.urlretrieve(url, out)
        print('Fetched:', path)
"
```

---

## Quick Reference: Root Raw URL

- **Docs root:** `https://raw.githubusercontent.com/google/adk-docs/main/docs/`
- **Single file:** `https://raw.githubusercontent.com/google/adk-docs/main/docs/<path/to/file>.md`
