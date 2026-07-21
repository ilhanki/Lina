from lina.interfaces.qt.worker import FunctionWorker


def test_cancelled_worker_never_starts_callable() -> None:
    calls: list[str] = []
    worker = FunctionWorker(lambda: calls.append("called"))
    worker.cancel()
    worker.run()
    assert calls == []


def test_worker_suppresses_result_after_cancellation() -> None:
    received: list[object] = []
    worker: FunctionWorker

    def operation() -> str:
        worker.cancel()
        return "late result"

    worker = FunctionWorker(operation)
    worker.signals.result.connect(received.append)
    worker.run()
    assert received == []


def test_worker_suppresses_error_after_cancellation() -> None:
    received: list[object] = []
    worker: FunctionWorker

    def operation() -> None:
        worker.cancel()
        raise RuntimeError("late error")

    worker = FunctionWorker(operation)
    worker.signals.error.connect(received.append)
    worker.run()
    assert received == []
