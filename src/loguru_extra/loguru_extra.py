import inspect
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Iterator, TypeVar

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])

TRACE_ID_KEY = "traceId"

_FORMAT_TEMPLATE = ("<green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> "
                    "<r>|</r> <le><b>{trace}</b></le> "
                    "<r>|</r> {{thread.id}} <r>|</r> <y><b>{{thread.name: ^12}}</b></y> "
                    "<r>|</r> <level>{{level: <8}}</level> "
                    "<r>|</r> <cyan>{{name}}</cyan><r>:</r><cyan>{{function}}</cyan><r>:</r><cyan>{{line}}</cyan> "
                    "<r>-</r> <level>{{message}}</level>\n{{exception}}")

_FORMAT_WITH_TRACE = _FORMAT_TEMPLATE.format(trace="{extra[" + TRACE_ID_KEY + "]}")
_FORMAT_WITHOUT_TRACE = _FORMAT_TEMPLATE.format(trace="-")

_trace_id: ContextVar[str | None] = ContextVar("loguru_extra_trace_id", default=None)


def FORMAT(record: dict) -> str:
    """Default format: prints the trace id, or "-" for records logged outside a trace."""
    return _FORMAT_WITH_TRACE if TRACE_ID_KEY in record["extra"] else _FORMAT_WITHOUT_TRACE


def setup(sink: Any = sys.stdout, level: str | int = "INFO", **kwargs: Any) -> int:
    """Replace all loguru handlers with a single one using the loguru-extra format.

    Extra keyword arguments are passed to ``logger.add``. Returns the handler id.
    """
    logger.remove()
    return _add(sink, level, **kwargs)


def add_file_logger(file_name: str, level: str | int = "INFO", **kwargs: Any) -> int:
    """Add a file handler using the loguru-extra format.

    Extra keyword arguments (``rotation``, ``retention``, ``compression``, ...) are
    passed to ``logger.add``. Returns the handler id.
    """
    return _add(file_name, level, **kwargs)


def _add(sink: Any, level: str | int, **kwargs: Any) -> int:
    kwargs.setdefault("format", FORMAT)
    kwargs.setdefault("backtrace", True)
    # diagnose prints local variable values in tracebacks, which can leak secrets
    kwargs.setdefault("diagnose", False)
    return logger.add(sink, level=level, **kwargs)


def get_trace_id() -> str | None:
    """Return the trace id of the current context, or None outside a trace."""
    return _trace_id.get()


@contextmanager
def trace(trace_id: str | None = None) -> Iterator[str]:
    """Bind a trace id to every record logged inside the block.

    Without an explicit ``trace_id`` an enclosing trace is reused, otherwise a new
    id is generated. The previous id is restored on exit.
    """
    trace_id = trace_id or _trace_id.get() or str(uuid.uuid4())
    token = _trace_id.set(trace_id)
    try:
        with logger.contextualize(**{TRACE_ID_KEY: trace_id}):
            yield trace_id
    finally:
        _trace_id.reset(token)


def traceable(func: F) -> F:
    """Run each call of ``func`` (sync or async) inside ``trace()``."""
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace():
                return await func(*args, **kwargs)

        return async_wrapper  # type: ignore[return-value]

    @wraps(func)
    def wrapper(*args, **kwargs):
        with trace():
            return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
