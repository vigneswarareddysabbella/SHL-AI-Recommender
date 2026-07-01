# SHL AI Recommender

A beginner-friendly FastAPI project for the SHL AI Intern take-home assignment.

This app helps a user chat about a hiring need and recommends SHL assessments from a local catalog.

## What This Project Contains

```text
app/
  main.py          API routes and web pages
  models.py        Request and response schemas
  catalog.py       Loads the local SHL catalog
  recommender.py   Recommendation and chat logic

data/
  shl_catalog.json Local assessment catalog

tests/
  test_agent.py    Basic behavior tests

requirements.txt   Python packages and versions
APPROACH.md        Short explanation of the design
README.md          Run instructions
```

## Python Packages Used

These versions are pinned in `requirements.txt`:

| Package | Version | Why it is used |
|---|---:|---|
| fastapi | 0.115.6 | Builds the API endpoints |
| uvicorn | 0.34.0 | Runs the FastAPI server |
| pydantic | 2.10.4 | Validates request and response data |
| pytest | 8.3.4 | Runs tests |

## How To Run In VS Code

### Step 1: Open The Project

Open VS Code, then choose:

```text
File > Open Folder
```

Select this folder:

```text
C:\Users\vigne\Documents\Codex\2026-07-01\i
```

### Step 2: Open Terminal

In VS Code, open:

```text
Terminal > New Terminal
```

Make sure the terminal is inside the project folder:

```powershell
cd C:\Users\vigne\Documents\Codex\2026-07-01\i
```

### Step 3: Create Virtual Environment

Run this once:

```powershell
python -m venv .venv
```

This creates a folder named `.venv`. It may not print any success message. That is normal.

### Step 4: Activate Virtual Environment

If you are using **Command Prompt**, run:

```cmd
.venv\Scripts\activate.bat
```

If you are using **PowerShell**, run:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, you should see `(.venv)` at the start of the terminal line.

### Step 5: Install Packages

Run:

```powershell
python -m pip install -r requirements.txt
```

### Step 6: Start The Server

Run:

```powershell
python -m uvicorn app.main:app --reload
```

When it works, you will see something like:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

Keep this terminal open. The server runs inside this terminal.

## Open The App

Home page:

```text
http://127.0.0.1:8000/
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected health response:

```json
{"status":"ok"}
```

## How To Chat

Open:

```text
http://127.0.0.1:8000/
```

Click the **Chat** button.

Try this message:

```text
I am hiring a Python developer
```

If it asks for seniority, reply:

```text
Mid-level, around 2 years
```

Other examples:

```text
Hiring a mid-level Java developer who works with stakeholders
```

```text
Actually, add personality tests too
```

```text
What is the difference between OPQ32r and Verify G+ General Ability?
```

## API Test With Curl

Health:

```powershell
curl http://127.0.0.1:8000/health
```

Chat:

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Hiring a Java developer who works with stakeholders\"},{\"role\":\"assistant\",\"content\":\"Sure. What is the seniority level?\"},{\"role\":\"user\",\"content\":\"Mid-level, around 4 years\"}]}"
```

## Response Format

The `/chat` API always returns this structure:

```json
{
  "reply": "Assistant message here",
  "recommendations": [
    {
      "name": "Assessment name",
      "url": "Catalog URL",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

## Common Problems

### uvicorn is not recognized

Use this command instead:

```powershell
python -m uvicorn app.main:app --reload
```

### 404 Not Found on / page

Restart the server:

```powershell
Ctrl + C
python -m uvicorn app.main:app --reload
```

### PowerShell blocks Activate.ps1

Run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Design Summary

- The app is stateless.
- The server does not store chat sessions.
- Each `/chat` request sends the full conversation history.
- Recommendations come only from `data/shl_catalog.json`.
- The agent can clarify, recommend, refine, compare, refuse off-topic questions, and block basic prompt-injection attempts.
"# SHL-AI-Recommender" 
