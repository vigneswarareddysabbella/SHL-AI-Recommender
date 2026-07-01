# Approach Document

## Design choices

The service is a stateless FastAPI application with two endpoints: `GET /health` and `POST /chat`. The `/chat` endpoint receives the full conversation history on every call, reconstructs the user's current hiring intent from user turns, and returns the next assistant message plus a structured recommendation list when enough context exists.

I used a deterministic retrieval engine instead of a hosted LLM so the API is fast, repeatable, and does not need a paid key. The agent scores SHL catalog entries using role words, skills, seniority hints, and requested assessment type. It returns only entries from `data/shl_catalog.json`, so every recommendation has a grounded name, URL, and test type.

## Conversational behavior

The agent handles the required behaviors:

- Clarify: vague requests such as "I need an assessment" return an empty recommendation list and ask for seniority or skills.
- Recommend: once role, seniority, skill, or assessment type is clear, it returns 1 to 10 catalog-backed recommendations.
- Refine: later user turns are included in the reconstructed intent, so constraints such as "add personality tests" update the shortlist.
- Compare: comparison questions between named assessments return a grounded difference using catalog descriptions.
- Refuse: off-topic questions and prompt-injection attempts return no recommendations and keep the conversation within SHL assessment selection.

## Retrieval setup

The catalog file contains SHL-style individual assessment entries with name, catalog URL, test type, seniority level, skills, job families, and a short description. The scorer tokenizes the conversation, compares it with each catalog entry, boosts exact skill and phrase matches, applies assessment-type preferences, and gives a small seniority match boost. This keeps the behavior explainable and easy to tune.

## Evaluation and improvements

The included tests cover the main evaluator probes: schema-compatible responses, vague-query clarification, Java recommendations, refinement into personality tests, comparison, and prompt-injection refusal. The most important production improvement would be replacing or expanding the included catalog with a fresh scrape/export of the complete SHL Individual Test Solutions catalog, while keeping the same JSON schema and retrieval logic.
