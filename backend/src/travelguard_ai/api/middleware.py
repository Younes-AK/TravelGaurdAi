from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("travelguard_ai.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            latency_ms = (time.perf_counter() - started) * 1000.0
            decision = getattr(request.state, "decision", None)
            logger.info(
                "request_id=%s method=%s path=%s status_code=%s decision=%s latency_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                status_code,
                decision,
                latency_ms,
            )

            response = locals().get("response")
            if response is not None:
                response.headers["x-request-id"] = request_id
