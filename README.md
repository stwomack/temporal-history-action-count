# Temporal History Action Count

A Python tool to analyze Temporal workflow history files and count [Temporal Cloud billable actions](https://docs.temporal.io/cloud/pricing#action). This tool helps you understand the cost implications of your Temporal workflows by identifying and counting billable events.

## ⚠️ IMPORTANT DISCLAIMER

**THIS IS AN UNOFFICIAL TOOL AND NOT GUARANTEED TO GIVE ACCURATE ACTION / STORAGE COUNTS**

This tool is provided as-is for estimation purposes only. Temporal's actual billing may differ from the counts provided by this tool. Always refer to your official Temporal Cloud billing dashboard for accurate usage and costs. Use this tool at your own risk for estimation and analysis purposes only.

## Features

- Parse Temporal workflow history JSON files (both old and new formats)
- Count billable actions according to Temporal's billing model
- Handle special cases like:
  - Local activities (billed when workflow task completes)
  - Child workflow executions (billed at 2x rate)
  - Signal-with-start patterns
- Calculate workflow run duration
- Estimate storage size requirements
- Debug mode for detailed event analysis

## Installation

Install using uv:

```bash
uv add temporal-history-action-count
```

Or install directly from source:

```bash
git clone https://github.com/steveandroulakis/temporal-history-action-count
cd temporal-history-action-count
uv sync
```

## Usage

### Command Line

```bash
# Basic usage
uv run temporal-billable workflow_history.json

# With debug output
uv run temporal-billable workflow_history.json --debug
```
```bash
# With retry count included 
uv run temporal-billable -r workflow_history.json

# With debug output
uv run temporal-billable -r workflow_history.json --debug
```

### Example Output

```bash
$ uv run python -m temporal_history_action_count.billable_actions tests/event_histories/signalwithstart.json

Count of distinct Billable Events (Actions):
WorkflowExecutionStarted: 1
TimerStarted: 3
ActivityTaskScheduled: 3

Total number of Billable Events (Actions) found: 7
Total run duration: 0m13s
Total storage size (estimate): 3.85 KB
```

```bash
$ uv run python -m temporal_history_action_count.billable_actions tests/event_histories/local_activities.json

Count of distinct Billable Events (Actions):
WorkflowExecutionStarted: 1
LocalActivity: 1 (billable out of 3 LocalActivity events total)

Total number of Billable Events (Actions) found: 2
Total run duration: 0m0s
Total storage size (estimate): 0.90 KB
```

### Python API

```python
from temporal_history_action_count.billable_actions import parse_workflow_history

billable_actions, local_activity_count, events = parse_workflow_history("workflow_history.json")
print(f"Total billable actions: {len(billable_actions)}")
```

## Billable Event Types

The tool recognizes the following billable event types:

- WorkflowExecutionStarted
- WorkflowExecutionContinuedAsNew
- ActivityTaskScheduled
- TimerStarted
- WorkflowExecutionSignaled
- ExternalWorkflowExecutionSignaled
- UpsertWorkflowSearchAttributes
- ChildWorkflowExecutionStarted (billed at 2x rate)
- WorkflowExecutionUpdateAccepted
- MarkerRecorded (for local activities)

## Output

The tool provides:

1. **Billable Action Summary**: Count of each type of billable action
2. **Total Billable Actions**: Total number of actions that will be billed
3. **Run Duration**: Total workflow execution time
4. **Storage Estimate**: Estimated storage size in KB

## File Format Support

Supports both:
- New format: `{"events": [...]}`
- Old format: `[...]` (direct array of events)

## Testing

Sample workflow histories used for tests live in
[`tests/event_histories`](tests/event_histories). A description of what each
file demonstrates is available in [TESTING.md](TESTING.md).

Run the full test suite with:

```bash
uv run pytest
```

## Development

```bash
# Clone the repository
git clone https://github.com/steveandroulakis/temporal-history-action-count
cd temporal-history-action-count

# Install dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Lint code
uv run flake8
```

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related

Based on the original gist: https://gist.github.com/steveandroulakis/52336b37a298122ea343f1d882d8ddb6