from openhumming.trace.events import TraceEvent


def format_trace_event(event: TraceEvent) -> str:
    return f"{event.timestamp} | {event.event} | {event.payload}"
