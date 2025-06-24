# Temporal History Action Count Contribution Guide

## Repository Layout
- `src/temporal_history_action_count/` - Main Python package containing the billable action analysis tool
- `src/temporal_history_action_count/billable_actions.py` - Core module with analysis logic and CLI
- `src/temporal_history_action_count/__init__.py` - Package initialization and public API exports
- `pyproject.toml` - Project configuration, dependencies, and build settings
- `README.md` - Project documentation and usage instructions

## Running the Application
1. Install dependencies using uv:
   ```bash
   uv sync
   ```
2. Run the tool directly:
   ```bash
   uv run python -m temporal_history_action_count.billable_actions workflow_history.json
   ```
   Or with debug output:
   ```bash
   uv run python -m temporal_history_action_count.billable_actions workflow_history.json --debug
   ```
3. Install as a command-line tool:
   ```bash
   uv sync
   temporal-billable workflow_history.json
   ```

## Testing
- Tests use pytest framework:
  ```bash
  uv run pytest                    # run full test suite
  uv run pytest --cov             # run with coverage
  uv run pytest -v                # verbose output
  uv run pytest --watch           # watch for changes
  ```
- Test files should be placed in `tests/` directory
- Use `test_*.py` naming convention for test files

## Linting and Formatting
- Format code with Black:
  ```bash
  uv run black .
  ```
- Sort imports with isort:
  ```bash
  uv run isort .
  ```
- Lint with flake8:
  ```bash
  uv run flake8
  ```
- Run all formatting and linting:
  ```bash
  uv run black . && uv run isort . && uv run flake8
  ```

## Development Workflow
- This tool analyzes Temporal workflow history JSON files
- Key functions: `parse_workflow_history()`, `display_billable_summary()`, `calculate_payload_size()`
- Supports both old and new Temporal history file formats
- Handles special billing cases like local activities and signal-with-start patterns

## Commit Messages and Pull Requests
- Use clear commit messages describing the functional change
- Open PRs with description of **what changed** and **why**
- Include test coverage for new features
- Ensure all linting passes before submitting