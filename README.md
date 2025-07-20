# At the end of the day, the day's gonna end.

Example env:

```
OPENAI_API_KEY=
REDIS_PASSWORD=
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

---

# API Documentation

## Base URL
```
http://localhost:8000
```

## Character Generation

### Generate Characters
**POST** `/chat/characters/generate`

Generate AI characters with unique personalities, problems, and voice characteristics.

**Request Body:**
```json
{
  "theme": "relationship issues",
  "num_characters": 3
}
```

**Response:**
```json
{
  "theme": "relationship issues",
  "characters": [
    {
      "id": "uuid-string",
      "name": "Character Name",
      "mental_state": "feeling anxious about the future",
      "problem": "Detailed description of life challenges...",
      "problem_description": "anxiety about future",
      "background": "Character's life history...",
      "interaction_warning": "Topics to avoid",
      "voice_instructions": "speak in a trembling, anxious voice with frequent pauses",
      "voice_selection": "nova",
      "gender": "female",
      "shirt": "hoodie",
      "pants": "jeans",
      "body_type": "average",
      "accessories": ["glasses", "backpack"]
    }
  ]
}
```

## Zombie Interaction System

### Get Initial Message
**POST** `/zombie`

Get the character's opening statement without sending audio.

**Request Body:**
```json
{
  "character_id": "uuid-string",
  # no audio_file_path
}
```

**Response:**
```json
{
  "transcription": "",
  "character_response": "I'm really struggling with...",
  "emotional_change": 0,
  "emotional_state": 50,
  "session_ended": false
}
```

### Send Audio Interaction
**POST** `/zombie`

Send audio file and get character response with emotional state changes.

**Request Body:**
```json
{
  "character_id": "uuid-string",
  "audio_file_path": "/path/to/audio.wav"
}
```

**Response:**
```json
{
  "transcription": "What you said in the audio",
  "character_response": "Character's emotional response",
  "emotional_change": -5,
  "emotional_state": 45,
  "session_ended": false
}
```

## Text-to-Speech

### Generate Character Voice
**POST** `/tts`

Generate audio from text using character-specific voice settings.

**Request Body:**
```json
{
  "text": "Text to convert to speech",
  "character_id": "uuid-string",
  "stored_file_path": "/path/to/output.wav"
}
```

**Response:**
```
200 OK (no body)
```

## Speech-to-Text

### Transcribe Audio
**POST** `/stt`

Convert audio file to text.

**Request Body:**
```json
{
  "file_path": "/path/to/audio.wav"
}
```

**Response:**
```
"Transcribed text from audio"
```

## Data Management

### Cleanup All Data
**DELETE** `/chat/cleanup`

Delete all test data.

**Response:**
```json
{
  "message": "All data cleaned up successfully"
}
```

## Emotional State System

- **Range**: 0-100
- **0**: Completely enraged/hopeless
- **50**: Neutral
- **100**: Completely satisfied/hopeful
- **Session ends** when emotional state reaches 0 or 100

## Voice Options

Available TTS voices: `ash`, `ballad`, `fable`, `coral`, `onyx`, `nova`, `shimmer`, `verse`

## Error Responses

All endpoints return standard HTTP status codes:
- **200**: Success
- **400**: Bad request
- **404**: Not found
- **500**: Server error

Error response format:
```json
{
  "detail": "Error description"
}
```
