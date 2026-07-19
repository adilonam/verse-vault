# Agent Instructions

Follow these rules when working in this repo.

- **This app runs in a devcontainer.** Code and the app are executed inside a VS Code / Cursor Dev Container, not on the host machine.
- **Keep changes small.** Fix only what was asked for. Do not refactor or add extra files unless requested.
-**Run before you finish.** Start the app with `uvicorn app:app --reload` and confirm `/` returns the page when you change server or template code.
-use a good architecture for fast api
- read the schema of db of bible in bible-sqlite-schema.txt for bible-sqlite.db when adding or edit or delete add it to bible-sqlite-schema.txt 
- the app is desined to work on Target platform is Raspberry Pi Zero 2 W running Raspberry Pi OS Lite 64-bit. The device uses ARM64 architecture (AArch64), 512 MB RAM, microSD storage, LCD display 5inch IPS Display for Raspberry Pi, DPI interface, no Touch, 800x480, and physical keyboard input. Application should be optimized for low-memory embedded hardware and use SQLite for local data storage. No cloud dependency required.
- No External resources (internet required) this app will work offline
- Whenever a keyboard shortcut / key binding is added, changed, or removed in the app, also update KEYBOARD.md to match (keep KEYBOARD.md as the simple key → action list).
