import pytest
from src.error_reporting import ErrorGroupData, ErrorReport


def test_new_errors_found(cached_errors: ErrorReport):
    # given
    error_report_with_new_error = ErrorReport(
        {
            **cached_errors.error_groups,
            "key3": ErrorGroupData(1, "SomeNewError", "best_eta"),
        }
    )
    # when
    result = error_report_with_new_error.get_new_errors(
        former_report=cached_errors,
    )
    # then
    error_groups = result.error_groups
    assert len(error_groups) == 1
    assert "key3" in error_groups
    value = error_groups["key3"]
    assert value.count == 1
    assert value.message == "SomeNewError"
    assert value.affected_service == "best_eta"


def test_spiked_errors_found(cached_errors: ErrorReport):
    # given
    threshold = 0.5
    error_report_with_spike = ErrorReport(
        {
            **cached_errors.error_groups,
            "key1": ErrorGroupData(50, "DatabaseError", "best_eta"),
        }
    )
    # when
    result = error_report_with_spike.get_spiked_errors(
        former_report=cached_errors,
        increase_threshold=threshold,
    )
    # then
    error_groups = result.error_groups
    assert len(error_groups) == 1
    assert "key1" in error_groups
    value = error_groups["key1"]
    assert value.count == 50
    assert value.message == "DatabaseError"
    assert value.affected_service == "best_eta"


def test_serialization(cached_errors: ErrorReport):
    # given
    serialized = cached_errors.serialize_error_report()
    # when
    deserialized = ErrorReport.deserialize_error_report(serialized)
    # then
    assert cached_errors.error_groups == deserialized.error_groups


@pytest.fixture
def cached_errors() -> ErrorReport:
    return ErrorReport(
        {
            "key1": ErrorGroupData(5, "DatabaseError", "best_eta"),
            "key2": ErrorGroupData(20, "SomeOtherError", "ecu_worldwide_pulling"),
        }
    )
