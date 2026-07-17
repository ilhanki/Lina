from lina.services.local_storage_service import LocalStorageService, format_storage_size


def test_local_storage_measurement_is_real_bounded_and_cached(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "one.bin").write_bytes(b"1234")
    (data / "two.bin").write_bytes(b"12")
    service = LocalStorageService((data,), max_entries=10, cache_seconds=60)
    first = service.measure()
    (data / "later.bin").write_bytes(b"ignored by cache")
    second = service.measure()
    assert first == second
    assert first.total_bytes == 6 and first.file_count == 2
    assert format_storage_size(2048) == "2.0 KB"


def test_local_storage_measurement_stops_at_entry_bound(tmp_path):
    for index in range(3):
        (tmp_path / f"{index}.txt").write_text("x", encoding="utf-8")
    snapshot = LocalStorageService((tmp_path,), max_entries=2, cache_seconds=0).measure()
    assert snapshot.file_count == 2
    assert snapshot.truncated is True
