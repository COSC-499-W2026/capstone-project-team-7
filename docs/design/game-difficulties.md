# Game difficulty foundation

`src/backend/difficulties.py` defines the shared `Difficulty` string enum and
`get_clue_rules(difficulty)` for clue composition and game services.

| Difficulty | Include spoken room number | Include description |
|---|---|---|
| `basic` | Yes | No |
| `advanced` | Yes | Yes |
| `expert` | No | Yes |

Values must match the lowercase identifiers exactly. Unsupported values raise
`ValueError`; future Pydantic request models can use `Difficulty` as a field type
to reject invalid inputs through FastAPI's standard 422 validation response.
Returned rules are immutable so callers cannot change shared difficulty behavior.

`utils/clue_text.py` composes the required fields using these rules and rejects
blank required content. `python -m utils.generate_audio` generates French demo
clips for every difficulty. Basic keeps the existing language/location path;
Advanced and Expert use a difficulty subfolder. Playback still uses Basic audio;
connecting playback to the saved game difficulty is follow-up work.

Run the focused tests with `python -m pytest tests/backend/test_difficulties.py tests/backend/test_clue_text.py tests/backend/test_generate_audio.py tests/backend/test_audio_storage.py`.
