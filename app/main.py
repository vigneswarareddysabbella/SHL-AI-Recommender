from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.models import ChatRequest, ChatResponse
from app.recommender import AssessmentAgent

app = FastAPI(title="Conversation Recommender", version="1.0.0")
agent = AssessmentAgent()


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\" />\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n  <title>SHL AI Recommender</title>\n  <style>\n    :root { color-scheme: light; font-family: Arial, Helvetica, sans-serif; }\n    body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f7faf6; color: #263126; }\n    main { width: min(92vw, 560px); text-align: center; padding: 32px 20px; }\n    h1 { margin: 0 0 14px; font-size: clamp(28px, 6vw, 48px); line-height: 1.1; font-weight: 700; }\n    p { margin: 0 auto 28px; max-width: 44ch; color: #586258; font-size: clamp(15px, 3vw, 18px); line-height: 1.5; }\n    a { display: inline-flex; align-items: center; justify-content: center; min-height: 56px; min-width: min(260px, 86vw); padding: 0 28px; border-radius: 8px; background: #3f7f2a; color: white; text-decoration: none; font-size: 18px; font-weight: 700; box-shadow: 0 10px 26px rgba(41, 86, 28, 0.22); }\n    a:focus, a:hover { background: #346f22; outline: 3px solid rgba(63, 127, 42, 0.22); outline-offset: 4px; }\n  </style>\n</head>\n<body>\n  <main>\n    <h1>SHL AI Recommender</h1>\n    <p>Find a grounded shortlist of SHL assessments through a simple chat.</p>\n    <a href=\"/playground\">Chat</a>\n  </main>\n</body>\n</html>"


@app.get("/playground", response_class=HTMLResponse)
def playground() -> str:
    return "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\" />\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n  <title>Chat | SHL AI Recommender</title>\n  <style>\n    :root { font-family: Arial, Helvetica, sans-serif; color: #263126; background: #f7faf6; }\n    body { margin: 0; min-height: 100vh; display: grid; grid-template-rows: auto 1fr auto; }\n    header { padding: 18px 20px; border-bottom: 1px solid #dfe8dc; background: white; }\n    header a { color: #3f7f2a; text-decoration: none; font-weight: 700; }\n    main { width: min(920px, 100%); margin: 0 auto; padding: 20px; box-sizing: border-box; }\n    #messages { display: grid; gap: 12px; padding-bottom: 120px; }\n    .msg { max-width: 760px; padding: 14px 16px; border-radius: 8px; line-height: 1.45; white-space: pre-wrap; }\n    .user { justify-self: end; background: #3f7f2a; color: white; }\n    .assistant { justify-self: start; background: white; border: 1px solid #dfe8dc; }\n    form { position: sticky; bottom: 0; display: flex; gap: 10px; padding: 16px 20px; background: rgba(247, 250, 246, 0.96); border-top: 1px solid #dfe8dc; }\n    input { flex: 1; min-width: 0; min-height: 48px; padding: 0 14px; border: 1px solid #b9c8b5; border-radius: 8px; font-size: 16px; }\n    button { min-height: 48px; padding: 0 20px; border: 0; border-radius: 8px; background: #3f7f2a; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }\n    button:hover { background: #346f22; }\n    @media (max-width: 560px) { form { padding: 12px; } button { padding: 0 14px; } }\n  </style>\n</head>\n<body>\n  <header><a href=\"/\">SHL AI Recommender</a></header>\n  <main><div id=\"messages\"><div class=\"msg assistant\">Tell me the role, seniority, and skills you want to assess.</div></div></main>\n  <form id=\"chatForm\">\n    <input id=\"messageInput\" autocomplete=\"off\" placeholder=\"Example: Hiring a mid-level Java developer\" />\n    <button type=\"submit\">Send</button>\n  </form>\n  <script>\n    const messages = [];\n    const list = document.getElementById('messages');\n    const form = document.getElementById('chatForm');\n    const input = document.getElementById('messageInput');\n\n    function addMessage(role, content) {\n      const div = document.createElement('div');\n      div.className = 'msg ' + role;\n      div.textContent = content;\n      list.appendChild(div);\n      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });\n    }\n\n    form.addEventListener('submit', async (event) => {\n      event.preventDefault();\n      const text = input.value.trim();\n      if (!text) return;\n      input.value = '';\n      messages.push({ role: 'user', content: text });\n      addMessage('user', text);\n      try {\n        const response = await fetch('/chat', {\n          method: 'POST',\n          headers: { 'Content-Type': 'application/json' },\n          body: JSON.stringify({ messages })\n        });\n        const data = await response.json();\n        const recs = data.recommendations && data.recommendations.length\n          ? '\\n\\nRecommendations:\\n' + data.recommendations.map((r, i) => (i + 1) + '. ' + r.name + ' (' + r.test_type + ')\\n' + r.url).join('\\n')\n          : '';\n        const reply = data.reply + recs;\n        messages.push({ role: 'assistant', content: data.reply });\n        addMessage('assistant', reply);\n      } catch (error) {\n        addMessage('assistant', 'Something went wrong. Please check the server terminal.');\n      }\n    });\n  </script>\n</body>\n</html>"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return agent.reply(request.messages)
