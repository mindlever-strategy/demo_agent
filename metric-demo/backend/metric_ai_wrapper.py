import os
import logging

_LOG = logging.getLogger(__name__)


def _is_serverless() -> bool:
    return os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None


def flush_metricai():
    """Wait for pending MetricAI telemetry before serverless runtimes freeze."""
    if not _is_serverless():
        return
    try:
        import metricai

        metricai.get_metricai().shutdown()
    except Exception:
        pass


def register_user(user_id: str, name: str, role: str):
    pass


def register_session(session_id: str, user_id: str):
    pass
