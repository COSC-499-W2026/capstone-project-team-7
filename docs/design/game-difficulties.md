# Game difficulty foundation

`src/backend/difficulties.py` defines the shared `Difficulty` string enum and
`get_clue_rules(difficulty)` for future game services.

| Difficulty | Include spoken room number | Include description |
|---|---|---|
| `basic` | Yes | No |
| `advanced` | Yes | Yes |
| `expert` | No | Yes |

Values must match the lowercase identifiers exactly. Unsupported values raise
`ValueError`; future Pydantic request models can use `Difficulty` as a field type
to reject invalid inputs through FastAPI's standard 422 validation response.
Returned rules are immutable so callers cannot change shared difficulty behavior.

This foundation does not yet select or generate clues, store locations, expose
game endpoints, or enforce session rules. Replay limits, photo attempts, timers,
and scoring remain future work pending confirmation of their values.

Run the focused tests with `python -m pytest tests/backend/test_difficulties.py`.
