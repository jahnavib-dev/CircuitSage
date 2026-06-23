# CircuitSage Context and Coding Rules

Welcome to the **CircuitSage** project. This file establishes the development guidelines, security constraints, and stylistic practices that all files in this codebase must adhere to.

---

## 1. Project Identity & Branding
* **Branding**: The project name is **CircuitSage** and must be spelled exactly as such.
* **Component Prefixes**: All agents must use the `CircuitSage` prefix in logs, user interface elements, and debug outputs.
  * Orchestrator agent: `CircuitSage` or `CircuitSage·Orchestrator`
  * Query specialist: `CircuitSage·Query`
  * Compare specialist: `CircuitSage·Compare`
  * Suggest specialist: `CircuitSage·Suggest`
* **Headers & Docstrings**: Every source file must begin with a docstring or header stating that it is part of the CircuitSage project.

---

## 2. Security Constraints
* **No Hardcoded Secrets**: Under no circumstances should API keys, passwords, or hostnames be hardcoded. Use `python-dotenv` to load secrets from the environment.
* **Input Validation & Sanitization**:
  * All text inputs submitted to any agent must be sanitized and capped at a maximum of **500 characters** before processing.
  * Check file paths passed to ingestion tools to prevent path traversal or processing of unauthorized file locations.
* **Error Handling**:
  * All agent interactions, vector search operations, and tool calls must be wrapped in `try/except` blocks to handle exceptions gracefully.
  * Do not expose raw, unsanitized stack traces to the user interface. Return user-friendly error messages with the agent prefix.

---

## 3. Code Style & Quality
* **Asynchronous Execution**: Agent executions (`run_async`) and external operations should leverage Python's `asyncio` framework.
* **Python Types**: Use strict type hints for all function signatures and tool definitions.
* **Documentation**: Include inline comments and docstrings explaining core engineering decisions, schemas, and processing logic.
