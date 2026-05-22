import functools
import json
import logging
import asyncio
from typing import Any, Callable

from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

logger = logging.getLogger(__name__)

# Obtain a tracer for manual instrumentation
tracer = trace.get_tracer("insight-pilot-tracer")

def _safe_serialize(obj: Any) -> str:
    """Helper to safely serialize function arguments and returns."""
    try:
        if hasattr(obj, "model_dump_json"):
            return obj.model_dump_json()
        elif hasattr(obj, "json"):
            return obj.json()
        elif hasattr(obj, "to_dict"):
            return json.dumps(obj.to_dict(), default=str)
        elif hasattr(obj, "__dict__"):
            return json.dumps(obj.__dict__, default=str)
        else:
            return json.dumps(obj, default=str)
    except Exception:
        return str(obj)

def _enrich_span(span: trace.Span, span_kind: OpenInferenceSpanKindValues, component: str, *args, **kwargs):
    """Adds common attributes to the span according to OpenInference conventions."""
    span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, span_kind.value)
    span.set_attribute("component", component)
    
    # Try capturing Chainlit session if available
    try:
        import chainlit as cl
        if cl.user_session:
            session_id = cl.user_session.get("id")
            if session_id:
                span.set_attribute(SpanAttributes.SESSION_ID, session_id)
            user = cl.user_session.get("user")
            if user:
                span.set_attribute("user_id", user.identifier if hasattr(user, 'identifier') else str(user))
    except Exception:
        pass
        
    # Capture Inputs
    input_data = {
        "args": [_safe_serialize(a) for a in args],
        "kwargs": {k: _safe_serialize(v) for k, v in kwargs.items()}
    }
    span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(input_data))

def trace_operation(span_kind: OpenInferenceSpanKindValues, name: str = None, component: str = "generic"):
    """
    Core decorator to trace a function execution safely, capturing args, 
    returns, exceptions, and latency (automatically handled by OTEL Span).
    """
    def decorator(func: Callable):
        span_name = name or func.__name__

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name) as span:
                    _enrich_span(span, span_kind, component, *args, **kwargs)
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute(SpanAttributes.OUTPUT_VALUE, _safe_serialize(result))
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name) as span:
                    _enrich_span(span, span_kind, component, *args, **kwargs)
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute(SpanAttributes.OUTPUT_VALUE, _safe_serialize(result))
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise
            return sync_wrapper
    return decorator

# --- Reusable Wrappers ---

def trace_chain(name: str = None):
    """Wrapper for higher-level execution chains or graphs."""
    return trace_operation(OpenInferenceSpanKindValues.CHAIN, name, component="chain")

def trace_node(name: str = None):
    """Wrapper for individual graph nodes."""
    return trace_operation(OpenInferenceSpanKindValues.CHAIN, name, component="graph_node")

def trace_tool(name: str = None):
    """Wrapper for generic tools or executors like BigQuery."""
    return trace_operation(OpenInferenceSpanKindValues.TOOL, name, component="tool")

def trace_retriever(name: str = None):
    """Wrapper for document retrievals (Confluence, PGVector, etc.)."""
    return trace_operation(OpenInferenceSpanKindValues.RETRIEVER, name, component="retriever")
