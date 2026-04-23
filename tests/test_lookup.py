import os
from pathlib import Path

from app import LookupStatus, lookup_latest_result, parse_result_file


def write_file(path: Path, content: str = "") -> None:
    path.write_text(content, encoding="utf-8")


def test_parse_result_file_supports_passed_and_failed_names(tmp_path: Path) -> None:
    passed = tmp_path / "20260423T100000Z_PASSED_SN1001.txt"
    failed = tmp_path / "20260423T100001Z_FAILED_SN1001.txt"
    write_file(passed)
    write_file(failed)

    parsed_passed = parse_result_file(passed)
    parsed_failed = parse_result_file(failed)

    assert parsed_passed is not None
    assert parsed_passed.serial == "SN1001"
    assert parsed_passed.status == LookupStatus.PASS

    assert parsed_failed is not None
    assert parsed_failed.serial == "SN1001"
    assert parsed_failed.status == LookupStatus.FAIL


def test_lookup_no_result(tmp_path: Path) -> None:
    write_file(tmp_path / "20260423T100000Z_PASSED_SN1001.txt")

    result = lookup_latest_result(tmp_path, "SN404")

    assert result.status == LookupStatus.NO_RESULT


def test_lookup_uses_latest_timestamp(tmp_path: Path) -> None:
    write_file(tmp_path / "20260423T100000Z_PASSED_SN2000.txt")
    write_file(tmp_path / "20260423T110000Z_FAILED_SN2000.txt")

    result = lookup_latest_result(tmp_path, "SN2000")

    assert result.status == LookupStatus.FAIL


def test_lookup_falls_back_to_mtime_when_no_timestamp(tmp_path: Path) -> None:
    older = tmp_path / "PASSED_SN3000.txt"
    newer = tmp_path / "FAILED_SN3000.txt"
    write_file(older)
    write_file(newer)

    os.utime(older, (1000, 1000))
    os.utime(newer, (2000, 2000))

    result = lookup_latest_result(tmp_path, "SN3000")

    assert result.status == LookupStatus.FAIL
