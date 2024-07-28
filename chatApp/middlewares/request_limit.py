import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from chatApp.config.logs import logger  # Import your custom logger


class RequestLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_requests: int = 4, window_seconds: int = 1):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_history: dict[str, tuple[int, float]] = defaultdict(
            lambda: (0, 0.0)
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Log request start time
        logger.info(f"Received request from {client_ip} at {current_time}")

        # Get the request count and last request time for this IP
        count, last_request_time = self.request_history[client_ip]

        # If it's been longer than the window, reset the count
        if current_time - last_request_time > self.window_seconds:
            count = 0

        # Increment the count
        count += 1

        # Update the request history
        self.request_history[client_ip] = (count, current_time)

        # If the count exceeds the limit, return a 429 Too Many Requests response
        if count > self.max_requests:
            logger.warning(f"Too many requests from {client_ip} - Count: {count}")
            return Response("Too many requests", status_code=429)

        # Measure start time of request processing
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate process time
        process_time = time.time() - start_time

        # Log the request processing time
        logger.info(f"Processed request from {client_ip} in {process_time:.4f} seconds")

        # Add X-Process-Time header to the response
        response.headers["X-Process-Time"] = str(process_time)

        return response
