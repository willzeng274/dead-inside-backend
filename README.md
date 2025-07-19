# At the end of the day, the day's gonna end.

Example env:

```
OPENAI_API_KEY=
```

## Stuff

```sh
uv venv
# then source or some windows activation thing

# install all deps
uv sync

# Add deps
uv add ...

# Remove deps
uv remove ...

# Add dev deps
uv add --dev ...

# Run server
uv run -- uvicorn app.main:app --reload

# Run tests
PYTHONPATH=. pytest -v -s
```

## Character Generation

Generate therapy characters from themes:

```sh
# Generate characters
POST /characters/generate
{
  "theme": "college students struggling with mental health"
}

# Response includes 3-5 characters with:
# - name, background, problems, mental_state
# - clothing: shirt, pants, body_type, accessories  
# - interaction_warning for therapy sessions
```

## Chat API

Therapy session endpoints for character interactions:

```sh
# Start new conversation
POST /chat/conversations
{
  "message": "Hello, how are you feeling today?",
  "character_context": {
    "name": "Alex",
    "mental_state": "anxious and overwhelmed",
    "problems": "work stress, relationship issues",
    "background": "recently divorced, struggling with career",
    "interaction_warning": "avoid discussing ex-partner"
  }
}

# Continue conversation
POST /chat/conversations/{id}/messages
{
  "message": "That sounds really difficult. Can you tell me more?",
  "character_context": { ... }
}

# List all conversations
GET /chat/conversations

# Get conversation details
GET /chat/conversations/{id}

# Delete conversation
DELETE /chat/conversations/{id}
```

Response includes emotional state changes and session status.