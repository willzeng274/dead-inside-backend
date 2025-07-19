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