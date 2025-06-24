# Test workflow history with local activities:
# https://gist.github.com/steveandroulakis/52336b37a298122ea343f1d882d8ddb6
# by https://github.com/steveandroulakis

import collections
import json
import sys
from datetime import datetime
from operator import itemgetter

# Constants for billable event types
BILLABLE_EVENT_TYPES = {
    "WorkflowExecutionStarted",
    "WorkflowExecutionContinuedAsNew",
    "ActivityTaskScheduled",
    "TimerStarted",
    "WorkflowExecutionSignaled",
    "ExternalWorkflowExecutionSignaled",
    "UpsertWorkflowSearchAttributes",
    "ChildWorkflowExecutionStarted",
    "WorkflowExecutionUpdateAccepted",
    "MarkerRecorded",
    # Older Temporal Server event types
    "EVENT_TYPE_WORKFLOW_EXECUTION_STARTED",
    "EVENT_TYPE_WORKFLOW_EXECUTION_CONTINUED_AS_NEW",
    "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED",
    "EVENT_TYPE_TIMER_STARTED",
    "EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED",
    "EVENT_TYPE_EXTERNAL_WORKFLOW_EXECUTION_SIGNALED",
    "EVENT_TYPE_UPSERT_WORKFLOW_SEARCH_ATTRIBUTES",
    "EVENT_TYPE_CHILD_WORKFLOW_EXECUTION_STARTED",
    "EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED",
    "EVENT_TYPE_MARKER_RECORDED",
}


def normalize_event_type(event_type):
    """
    Normalize event type to ensure compatibility between different file formats.
    """
    event_type_mapping = {
        "EVENT_TYPE_WORKFLOW_EXECUTION_STARTED": "WorkflowExecutionStarted",
        "EVENT_TYPE_WORKFLOW_EXECUTION_CONTINUED_AS_NEW": (
            "WorkflowExecutionContinuedAsNew"
        ),
        "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED": "ActivityTaskScheduled",
        "EVENT_TYPE_TIMER_STARTED": "TimerStarted",
        "EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED": "WorkflowExecutionSignaled",
        "EVENT_TYPE_EXTERNAL_WORKFLOW_EXECUTION_SIGNALED": (
            "ExternalWorkflowExecutionSignaled"
        ),
        "EVENT_TYPE_UPSERT_WORKFLOW_SEARCH_ATTRIBUTES": (
            "UpsertWorkflowSearchAttributes"
        ),
        "EVENT_TYPE_CHILD_WORKFLOW_EXECUTION_STARTED": "ChildWorkflowExecutionStarted",
        "EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED": (
            "WorkflowExecutionUpdateAccepted"
        ),
        "EVENT_TYPE_MARKER_RECORDED": "MarkerRecorded",
        "EVENT_TYPE_WORKFLOW_TASK_COMPLETED": "WorkflowTaskCompleted",
    }
    return event_type_mapping.get(event_type, event_type)


def is_local_activity_marker(event):
    """
    Check if the event is a local activity marker.
    """
    marker_attributes = event.get("markerRecordedEventAttributes", {})

    return normalize_event_type(
        event["eventType"]
    ) == "MarkerRecorded" and marker_attributes.get("markerName") in {
        "core_local_activity",
        "LocalActivity",
    }


def process_event(
    event, has_local_activity, local_activity_count, billable_actions, debug
):
    """
    Process an individual event to determine if it's billable.
    """
    # Normalize event type
    normalized_event_type = normalize_event_type(event["eventType"])

    if normalized_event_type == "WorkflowTaskCompleted" and has_local_activity:
        billable_actions.append("LocalActivity")
        has_local_activity = False
        if debug:
            print(f"\t BILLABLE (preceding workflow task contains Local Activities)")
    elif normalized_event_type in BILLABLE_EVENT_TYPES:
        if normalized_event_type == "ChildWorkflowExecutionStarted":
            # Double count the ChildWorkflowExecutionStarted event
            billable_actions.append(normalized_event_type)
            billable_actions.append(normalized_event_type)
            if debug:
                print(f"\t BILLABLE (at 2x)")
        elif normalized_event_type == "MarkerRecorded":
            if is_local_activity_marker(event):
                # if it's a MarkerRecorded event for a local activity
                has_local_activity = True
                local_activity_count += 1
            else:
                # Other MarkerRecorded events like SideEffect/Version are not billable
                pass
        else:
            billable_actions.append(normalized_event_type)
            if debug:
                print(f"\t BILLABLE")

    return has_local_activity, local_activity_count


def is_signal_with_start(events):
    """
    Check if this workflow uses signal-with-start pattern.
    Signal-with-start means WORKFLOW_EXECUTION_SIGNALED immediately follows
    WORKFLOW_EXECUTION_STARTED before any WORKFLOW_TASK_SCHEDULED.
    """
    if len(events) < 3:
        return False

    # Check first three events for the pattern
    first_event = normalize_event_type(events[0]["eventType"])
    second_event = normalize_event_type(events[1]["eventType"])

    return (
        first_event == "WorkflowExecutionStarted"
        and second_event == "WorkflowExecutionSignaled"
    )


def parse_workflow_history(filename, debug=False):
    """
    Parse the workflow history from a given filename and count billable actions.
    Supports both old and new file formats
    """
    with open(filename, "r") as file:
        data = json.load(file)

    # Detect file format and extract events
    if isinstance(data, dict):
        # New format
        events = data["events"]
    elif isinstance(data, list):
        # Old format
        events = data
    else:
        raise ValueError("Unsupported file format")

    billable_actions = []
    has_local_activity = False
    local_activity_count = 0

    # Check for signal-with-start pattern
    signal_with_start = is_signal_with_start(events)
    signal_with_start_processed = False

    for event in events:
        if debug:
            print(f"event {event['eventId']}: evaluating {event['eventType']}")

        normalized_event_type = normalize_event_type(event["eventType"])

        # Handle signal-with-start: treat STARTED+SIGNALED as single billable action
        if signal_with_start:
            if (
                normalized_event_type == "WorkflowExecutionStarted"
                and not signal_with_start_processed
            ):
                billable_actions.append("WorkflowExecutionStarted")
                if debug:
                    print(f"\t BILLABLE (signal-with-start pattern)")
                signal_with_start_processed = True
                continue
            elif (
                normalized_event_type == "WorkflowExecutionSignaled"
                and signal_with_start_processed
            ):
                # Skip the signaled event in signal-with-start pattern
                if debug:
                    print(f"\t SKIPPED (part of signal-with-start pattern)")
                continue

        has_local_activity, local_activity_count = process_event(
            event, has_local_activity, local_activity_count, billable_actions, debug
        )

    # Capture any pending local activity as billable
    if has_local_activity:
        billable_actions.append("LocalActivity")
        if debug:
            print(f"\t BILLABLE (preceding workflow task contains Local Activities)")

    return billable_actions, local_activity_count, events


def display_billable_summary(billable_actions, local_activity_count):
    """
    Print a summary of billable actions.
    """
    event_type_counts = collections.Counter(billable_actions)
    sorted_event_type_counts = sorted(
        event_type_counts.items(), key=itemgetter(1), reverse=False
    )

    print("\nCount of distinct Billable Events (Actions):")
    for action, count in sorted_event_type_counts:
        if action == "LocalActivity":
            print(
                f"{action}: {count} (billable out of {local_activity_count} "
                f"LocalActivity events total)"
            )
        else:
            print(f"{action}: {count}")

    print(f"\nTotal number of Billable Events (Actions) found: {len(billable_actions)}")


def calculate_payload_size(events):
    total_size = 0
    event_count = 1

    for event in events:
        dataInputResult = None

        # Checking for various event types and extracting 'input' or 'result'
        if "workflowExecutionStartedEventAttributes" in event:
            dataInputResult = event["workflowExecutionStartedEventAttributes"].get(
                "input"
            )
        elif "startChildWorkflowExecutionInitiatedEventAttributes" in event:
            dataInputResult = event[
                "startChildWorkflowExecutionInitiatedEventAttributes"
            ].get("input")
        elif "activityTaskScheduledEventAttributes" in event:
            dataInputResult = event["activityTaskScheduledEventAttributes"].get("input")
        elif "workflowExecutionSignaledEventAttributes" in event:
            dataInputResult = event["workflowExecutionSignaledEventAttributes"].get(
                "input"
            )
        elif "childWorkflowExecutionCompletedEventAttributes" in event:
            dataInputResult = event[
                "childWorkflowExecutionCompletedEventAttributes"
            ].get("result")
        elif "activityTaskCompletedEventAttributes" in event:
            dataInputResult = event["activityTaskCompletedEventAttributes"].get(
                "result"
            )
        elif "workflowExecutionCompletedEventAttributes" in event:
            dataInputResult = event["workflowExecutionCompletedEventAttributes"].get(
                "result"
            )
        elif "activityTaskFailedEventAttributes" in event:
            dataInputResult = (
                event["activityTaskFailedEventAttributes"]
                .get("failure")
                .get("encodedAttributes")
            )
        elif "workflowExecutionFailedEventAttributes" in event:
            dataInputResult = (
                event["workflowExecutionFailedEventAttributes"]
                .get("failure")
                .get("encodedAttributes")
            )

        # Calculate size if dataInputResult is not None
        if dataInputResult is not None:
            data_json = json.dumps(dataInputResult)
            size = len(data_json.encode("utf-8"))
            total_size += size
            # print(f"Event {event_count} Data size: {size} bytes")

        event_count += 1

    # print(f"Total size of data is {total_size} bytes")
    return total_size


def calculate_event_count_size(events):
    event_count = len(events)
    event_count_size = event_count * 78  # each event adds ~78 bytes
    # print(f"Event count: {event_count}, Event count size: {event_count_size} bytes")
    return event_count_size


def parse_event_time(event_time):
    if isinstance(event_time, dict):
        # The format with "seconds" and "nanos"
        return int(event_time["seconds"]) + int(event_time["nanos"]) / 1_000_000_000
    elif isinstance(event_time, str):
        # The ISO format
        return datetime.fromisoformat(event_time.rstrip("Z")).timestamp()
    else:
        raise ValueError("Unknown event time format")


def calculate_run_duration(events):
    if not events or len(events) < 2:
        return "0m0s"  # Default value for insufficient events

    # Parse start and end times
    start_seconds = parse_event_time(events[0]["eventTime"])
    end_seconds = parse_event_time(events[-1]["eventTime"])

    # Calculate duration in seconds
    duration_seconds = end_seconds - start_seconds

    # Convert to minutes and seconds
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    return f"{minutes}m{seconds}s"


def main():
    """
    CLI
    """
    if len(sys.argv) < 2:
        print("Usage: python billable_actions.py <Temporal history filename> [--debug]")
        sys.exit(1)

    filename = sys.argv[1]
    debug_mode = "--debug" in sys.argv
    billable_actions, local_activity_count, events = parse_workflow_history(
        filename, debug=debug_mode
    )
    display_billable_summary(billable_actions, local_activity_count)

    # Calculate and print the run duration
    run_duration = calculate_run_duration(events)
    print(f"Total run duration: {run_duration}")

    # Size calculations
    total_payload_size = calculate_payload_size(events)
    total_event_count_size = calculate_event_count_size(events)
    final_total = total_payload_size + total_event_count_size

    # Convert to kilobytes (KB) and print
    final_total_kb = final_total / 1024
    print(f"Total storage size (estimate): {final_total_kb:.2f} KB")


if __name__ == "__main__":
    main()
