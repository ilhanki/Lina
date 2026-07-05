# Lina Architecture

Lina is organized around isolated capability packages under `src/lina`.

The early project should evolve in layers:

1. Core application lifecycle, configuration, and logging.
2. Local LLM service integration.
3. Tool registry and execution contracts.
4. Memory storage and retrieval.
5. Speech input and text-to-speech output.
6. Vision and screen capture.
7. Windows automation.
8. Multi-agent orchestration.
9. Desktop GUI and optional API surfaces.

Each layer should expose clear interfaces and avoid depending on presentation code.

