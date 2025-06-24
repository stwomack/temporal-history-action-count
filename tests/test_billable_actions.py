import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

# Ensure the package in ../src is importable without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from temporal_history_action_count.billable_actions import (  # noqa: E402
    parse_workflow_history,
)

DATA_DIR = Path(__file__).parent / "event_histories"


@pytest.mark.parametrize(
    "filename,expected_count",
    [
        ("start_thensignal.json", 8),
        ("signalwithstart.json", 7),
        ("local_activities.json", 2),
        ("localActivityRetriesTypescript.json", 2),
        ("local_mutable_side_effect.json", 2),
        ("local_side_effect.json", 2),
        ("local_mutablemany_local_mutable.json", 2),
        ("over100LocalActivitiesTaskHeartbeat.json", 2),
        ("150_retries_150.json", 13),
        ("batch_parent.json", 125),
        ("batch_child.json", 51),
        ("agent.json", 17),
        ("transfer.json", 7),
        ("update_with_start.json", 4),
    ],
)
def test_parse_workflow_history_counts(filename, expected_count):
    actions, _, _ = parse_workflow_history(str(DATA_DIR / filename))
    assert len(actions) == expected_count


def test_debug_output(capsys):
    path = DATA_DIR / "start_thensignal.json"
    buf = io.StringIO()
    with redirect_stdout(buf):
        parse_workflow_history(str(path), debug=True)
    out = buf.getvalue()
    assert "event 1: evaluating" in out
    assert "BILLABLE" in out


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_workflow_history("non_existent.json")
