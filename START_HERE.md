# Hoopagami — Start Here

This is the Hoopagami NBA Statline Scorigami project.

Before making changes:
1. Read `HOOPAGAMI_HANDOFF.md`.
2. Read `HOOPAGAMI_CURRENT_STATE.md`.
3. Treat the actual files in the `Hoopagami` project as the source of truth.
4. Inspect existing code before changing it.
5. Make only 1–2 changes at a time.
6. Prefer Terminal commands for edits when practical rather than asking me to open files manually in TextEdit.
7. Test the app after each change.
8. Do not ask me to re-paste code that is already available in the project or documented in these files.

## Current project

The project is a local Python/Flask web app called Hoopagami.

Main files:
- `app.py`
- `templates/index.html`
- `templates/player_search.html`
- `templates/search.html`
- `templates/rarest.html`
- `templates/statline_detail.html`

The project tracks NBA player statlines and identifies "Hoopagamis": player statlines that occurred exactly once in the database.

The user cares about preserving the existing Hoopagami visual identity and making changes incrementally rather than rewriting working sections.

## Important rule

Do not make broad redesigns or large refactors unless specifically requested.

When proposing a change, explain briefly what it will change, then make the smallest practical edit and test it.
