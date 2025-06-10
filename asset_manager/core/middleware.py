# pylint: disable=too-few-public-methods
"""Module containing middleware to run in the application"""

import json
import time
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from asset_manager.core.logger import http_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests from users"""

    async def dispatch(self, request: Request, call_next: Any):
        """Called on each request"""
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        data: dict[str, Any] = {
            "type": request.scope.get("type"),
            "asgi": request.scope.get("asgi"),
            "http_version": request.scope.get("http_version"),
            "server": request.scope.get("server"),
            "client": request.scope.get("client"),
            "scheme": request.scope.get("scheme"),
            "query_string": request.scope.get("query_string"),
            "process_time": process_time,
        }

        http_logger.info(
            "%s - %s %s - %d - %s",
            request.scope["client"][0],
            request.method,
            request.url.path,
            response.status_code,
            json.dumps(data, default=str),
        )

        return response
