# Lina

Lina is a local-first desktop AI assistant project for Windows.

The project is intentionally modular so capabilities can grow independently:
local LLM chat, memory, speech, vision, automation, tools, agents, and future UI/API layers.

This repository currently contains architecture scaffolding only. Assistant behavior is not implemented yet.

## Naming Convention

- Python packages and modules use `snake_case`.
- Classes use `PascalCase`.
- Functions, methods, and variables use `snake_case`.
- Constants use `UPPER_SNAKE_CASE`.
- Tool modules should be named by capability, for example `file_search.py` or `browser_control.py`.
- Agent modules should be named by role, for example `planner_agent.py` or `research_agent.py`.
- Tests should mirror source modules with `test_<module_name>.py`.

## Project Principles

- Keep business logic independent from UI.
- Keep integrations isolated behind service or adapter modules.
- Prefer small modules with clear ownership.
- Treat configuration, logs, data, models, and cache as separate concerns.
- Add tests alongside each new capability.

