import asyncio
import os
import subprocess
import sys

import pytest

from loguru_extra import add_file_logger, get_trace_id, logger, trace, traceable


@pytest.fixture
def records():
    collected = []
    handler_id = logger.add(lambda m: collected.append(m.record), level="DEBUG", format="{message}")
    yield collected
    logger.remove(handler_id)


def trace_ids(records):
    return [r["extra"].get("traceId") for r in records]


def test_separate_calls_get_distinct_trace_ids(records):
    @traceable
    def handle():
        logger.info("request")

    handle()
    handle()

    first, second = trace_ids(records)
    assert first and second and first != second


def test_trace_id_is_cleared_after_call(records):
    @traceable
    def handle():
        logger.info("inside")

    handle()
    logger.info("outside")

    assert trace_ids(records)[1] is None
    assert get_trace_id() is None


def test_nested_calls_share_outer_trace_id(records):
    @traceable
    def inner():
        logger.info("inner")

    @traceable
    def outer():
        logger.info("before")
        inner()
        logger.info("after")

    outer()

    assert len(set(trace_ids(records))) == 1


def test_trace_id_is_cleared_after_exception():
    @traceable
    def fail():
        raise ValueError

    with pytest.raises(ValueError):
        fail()

    assert get_trace_id() is None


def test_async_function(records):
    @traceable
    async def handle():
        await asyncio.sleep(0)
        logger.info("async")

    asyncio.run(handle())

    assert trace_ids(records)[0] is not None


def test_concurrent_tasks_get_distinct_trace_ids(records):
    @traceable
    async def handle(n):
        await asyncio.sleep(0)
        logger.info("task {}", n)
        await asyncio.sleep(0)
        return get_trace_id()

    async def main():
        return await asyncio.gather(handle(1), handle(2))

    first, second = asyncio.run(main())

    assert first != second
    assert {first, second} == set(trace_ids(records))


def test_explicit_trace_id(records):
    with trace("req-42") as trace_id:
        logger.info("inside")

    assert trace_id == "req-42"
    assert trace_ids(records) == ["req-42"]


def test_traceable_preserves_metadata():
    @traceable
    def handle():
        """Docstring."""

    assert handle.__name__ == "handle"
    assert handle.__doc__ == "Docstring."


def test_file_logger_format(tmp_path):
    path = tmp_path / "app.log"
    handler_id = add_file_logger(str(path), level="DEBUG")
    try:
        logger.debug("no trace")
        with trace("abc"):
            logger.debug("with trace")
    finally:
        logger.remove(handler_id)

    no_trace, with_trace = path.read_text().splitlines()
    assert "| - |" in no_trace and no_trace.endswith("no trace")
    assert "| abc |" in with_trace and with_trace.endswith("with trace")


def test_import_keeps_existing_handlers():
    code = ("from loguru import logger\n"
            "handler_id = logger.add(lambda m: None)\n"
            "import loguru_extra\n"
            "logger.remove(handler_id)\n")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    subprocess.run([sys.executable, "-c", code], check=True, env=env)
