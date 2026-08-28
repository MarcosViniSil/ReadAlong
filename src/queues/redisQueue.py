"""Redis-backed queue for audio jobs.

The orchestrator (this repo) pushes one JSON message per chunk onto a
Redis list (FIFO). An external worker on another machine pops jobs from
that list, synthesizes the audio, and pushes a result JSON back onto a
second list. The orchestrator blocks until every chunk it published has
a matching result (correlated by ``chunk_id``).

Connection is configured via env vars so the Redis instance can live on
another computer (a "remote queue"):
  REDIS_HOST     (default localhost)
  REDIS_PORT     (default 6379)
  REDIS_DB       (default 0)
  REDIS_PASSWORD (default none)
"""
import json
import os
from dotenv import load_dotenv
load_dotenv()
import time

import redis

JOBS_KEY = "readalong:audio:jobs"
RESULTS_KEY = "readalong:audio:results"
DEFAULT_TIMEOUT = 300.0


class AudioQueue:
    """Minimal FIFO queue on top of Redis lists: jobs in, results out."""

    def __init__(self, client: redis.Redis | None = None):
        self.client = client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD") or None,
        )

    def publish_jobs(self, messages: list[dict]) -> None:
        """Push one JSON message per chunk onto the jobs list (tail)."""
        for message in messages:
            self.client.rpush(JOBS_KEY, json.dumps(message, ensure_ascii=False))

    def wait_for_results(self, expected_chunk_ids: set[str], timeout: float = DEFAULT_TIMEOUT) -> dict[str, dict]:
        """Block until every chunk_id in ``expected_chunk_ids`` has a result.

        The worker pushes results onto the results list (tail); we pop from
        the head, so results are consumed in arrival order. Results whose
        chunk_id we are not waiting for (e.g. from another book) are
        discarded — each pipeline run waits only for its own chunks.

        Returns {chunk_id: response_dict}. Raises TimeoutError if not all
        responses arrive within ``timeout`` seconds.
        """
        responses: dict[str, dict] = {}
        deadline = time.monotonic() + timeout

        while not expected_chunk_ids.issubset(responses.keys()):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                missing = expected_chunk_ids - responses.keys()
                raise TimeoutError(f"Timed out waiting for chunk ids: {sorted(missing)}")

            item = self.client.blpop(RESULTS_KEY, timeout=min(remaining, 5))
            if item is None:
                continue  # timed out waiting, loop re-checks the deadline

            _, raw = item
            response = json.loads(raw)
            chunk_id = response.get("chunk_id")
            if chunk_id in expected_chunk_ids:
                responses[chunk_id] = response

        return responses
