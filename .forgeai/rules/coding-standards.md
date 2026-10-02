# ForgeAI Coding Standards

## 1. General Principles

* Follow the existing project architecture and conventions.
* Prefer simple, readable, and maintainable implementations.
* Follow SOLID and DRY principles where appropriate.
* Do not introduce unnecessary abstractions.
* Do not modify unrelated files.
* Reuse existing utilities and dependencies when possible.
* Do not introduce a new dependency when the existing dependencies can solve the problem.

## 2. Python Standards

* Use Python 3.11+ syntax and features supported by the project.
* Use type annotations for functions, methods, parameters, and important variables.
* Prefer built-in generic types such as `list[str]`, `dict[str, Any]`, and `tuple[str, int]`.
* Use `|` for union types, such as `str | None`.
* Avoid `typing.Optional`, `typing.Union`, `typing.List`, and `typing.Dict`.
* Avoid `Any` unless the type genuinely cannot be determined.
* Follow Ruff-compatible formatting and linting conventions.

## 3. Functions and Classes

* Keep functions focused on a single responsibility.
* Keep functions reasonably small.
* Use descriptive names.
* Avoid deeply nested logic when it can be simplified.
* Add docstrings to public functions, methods, and classes.
* Use Google-style docstrings for Python code.
* Document parameters and return values when they provide useful information.
* Document exceptions when a function can intentionally raise them.

## 4. Error Handling

* Handle expected errors explicitly.
* Never use bare `except:` blocks.
* Do not silently ignore exceptions.
* Return meaningful error messages when appropriate for tool functions.
* Preserve the original exception context when re-raising exceptions.
* Do not use exceptions as normal control flow when another approach is clearer.

## 5. Imports

* Keep imports organized and compatible with Ruff.
* Use absolute imports within the ForgeAI package.
* Do not add comments above imports unless there is a specific reason.
* Remove unused imports.

## 6. Documentation

* Keep documentation concise and technically accurate.
* Do not add unnecessary comments.
* Prefer self-explanatory code over excessive comments.
* Comments should explain why something is done, not simply repeat what the code does.
* Keep public API documentation up to date when behavior changes.

## 7. Dependencies

* Use the versions and dependency constraints defined in `pyproject.toml`.
* Manage dependencies with `uv`.
* Do not manually modify `uv.lock`.
* Avoid adding dependencies for functionality that can reasonably be implemented using the existing stack.

## 8. ForgeAI Architecture

* Keep agent state definitions inside `forgeai/agent/`.
* Keep LangGraph graph construction inside `forgeai/agent/`.
* Keep CLI/UI behavior inside `forgeai/ui/`.
* Keep slash commands inside `forgeai/commands/`.
* Keep LangChain tools inside `forgeai/tools/`.
* Keep application configuration inside `forgeai/config/`.
* Keep user-facing agent prompts inside `.forgeai/prompts/`.
* Keep project-specific coding policies inside `.forgeai/rules/`.
* Keep persistent LangGraph checkpoint data inside `.forgeai/db/`.
* Keep ARCHITECT planning artifacts inside `.forgeai/plans/`.

## 9. Tool Development

* Every LangChain `@tool` function must have a clear docstring.
* Tool parameters must have useful descriptions.
* Validate tool inputs before performing operations.
* Return clear results or actionable error messages.
* Tools must not perform destructive operations without the required approval mechanism.
* Respect `.gitignore` when reading or listing project files.
* Avoid exposing secrets, credentials, tokens, or environment variables.

## 10. Testing and Validation

* Validate significant changes before considering them complete.
* Run relevant tests after modifying functionality.
* Run Ruff when appropriate.
* Verify imports after adding or changing modules.
* Do not claim that code was tested unless it was actually tested.

## 11. Changes

* Make the smallest change that correctly solves the requested problem.
* Preserve existing behavior unless the user explicitly requests a behavior change.
* Do not rewrite working code unnecessarily.
* Before modifying a file, understand how it is used by the rest of the application.
