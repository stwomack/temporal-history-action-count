# Testing Temporal History Action Count

This project uses **pytest** for automated testing. Test cases live in the
[`tests/`](tests/) directory. To install the development dependencies and run the
full test suite use the commands below.

```bash
uv sync            # install dependencies
uv run pytest      # run the tests
```

## Sample Event Histories

Workflow history examples used for tests are stored in
[`tests/event_histories`](tests/event_histories). Each file represents a specific
scenario that exercises the billing logic.

- [`start_thensignal.json`](tests/event_histories/start_thensignal.json) – counts
  a workflow start followed by a signal (two billable actions).
- [`signalwithstart.json`](tests/event_histories/signalwithstart.json) – shows
  the signal-with-start feature where the initial signal is combined with the
  start (one billable action instead of two).
- [`local_activities.json`](tests/event_histories/local_activities.json) –
  workflow containing three local activities but billed for one action.
- [`localActivityRetriesTypescript.json`](tests/event_histories/localActivityRetriesTypescript.json)
  – a local activity retried once; still billed as a single action.
- [`local_mutable_side_effect.json`](tests/event_histories/local_mutable_side_effect.json)
  – tests local mutable side effects with a single billable action.
- [`local_side_effect.json`](tests/event_histories/local_side_effect.json) –
  demonstrates local side effects counted as one action.
- [`local_mutablemany_local_mutable.json`](tests/event_histories/local_mutablemany_local_mutable.json)
  – multiple local mutables grouped into a single billable local activity.
- [`over100LocalActivitiesTaskHeartbeat.json`](tests/event_histories/over100LocalActivitiesTaskHeartbeat.json)
  – more than 100 local activities recorded via heartbeats but only one action is
  billed.
- [`150_retries_150.json`](tests/event_histories/150_retries_150.json) – a large
  number of local activity retries resulting in 12 billable actions plus the
  start event.
- [`batch_parent.json`](tests/event_histories/batch_parent.json) – parent
  workflow starting many child workflows and activities.
- [`batch_child.json`](tests/event_histories/batch_child.json) – a child workflow
  scheduling multiple activities.
- [`agent.json`](tests/event_histories/agent.json) – long running workflow with
  repeated activities.
- [`transfer.json`](tests/event_histories/transfer.json) – workflow with timers
  and activities used for basic counting.
- [`update_with_start.json`](tests/event_histories/update_with_start.json) –
  demonstrates a workflow update alongside a start event.

## Running Individual Examples

You can manually run the billable actions script against a history file:

```bash
uv run python -m temporal_history_action_count.billable_actions \
    tests/event_histories/start_thensignal.json --debug
```

The tests in `tests/test_billable_actions.py` ensure these histories produce the
expected billable action counts and that debug output is generated correctly.
