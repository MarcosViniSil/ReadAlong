from models.Job import Job
from models.enum.BookStatus import BookStatus
from models.enum.JobType import JobType
from storage.connection import Database
from storage.jobRepository.jobRepositoryProvider import JobRepositoryProvider


class JobRepositoryImpl(JobRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _job_from_row(row: dict) -> Job:
        return Job(
            id=str(row["id"]),
            processing_run_id=str(row["processing_run_id"]),
            page_id=str(row["page_id"]),
            chunk_id=str(row["chunk_id"]) if row["chunk_id"] else None,
            type=JobType(row["type"]),
            status=BookStatus(row["status"]),
            worker_id=str(row["worker_id"]) if row["worker_id"] else None,
            attempt=row["attempt"],
            queued_at=row["queued_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            error_code=row["error_code"],
            error_message=row["error_message"],
        )

    @staticmethod
    def _create_sql() -> str:
        return """
            INSERT INTO jobs (processing_run_id, page_id, chunk_id, type, status)
            SELECT p.processing_run_id, c.page_id, c.id, 'generate_audio', 'pending'
            FROM chunks c
            JOIN pages p ON p.id = c.page_id
            WHERE c.id = %s::uuid
            RETURNING *
        """

    async def create(self, chunk_id) -> Job:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(self._create_sql(), [chunk_id])
        return self._job_from_row(row)

    async def create_many(self, chunk_ids: list[int]) -> list[Job]:
        created = []
        async with self._db.transaction() as tx:
            for chunk_id in chunk_ids:
                row = await tx.fetchone(self._create_sql(), [chunk_id])
                created.append(self._job_from_row(row))
        return created

    async def get_by_id(self, chunk_id) -> Job | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM jobs WHERE chunk_id = %s::uuid",
                [chunk_id],
            )
        return self._job_from_row(row) if row else None

    async def claim(self, job_id, worker_id) -> Job | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                UPDATE jobs
                SET worker_id = %s, status = 'processing', started_at = now()
                WHERE id = %s::uuid AND status = 'pending'
                RETURNING *
                """,
                [worker_id, job_id],
            )
        return self._job_from_row(row) if row else None

    async def mark_processing(self, job_id) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE jobs SET status = 'processing', started_at = now() WHERE id = %s::uuid",
                [job_id],
            )

    async def mark_completed(self, job_id) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE jobs SET status = 'completed', finished_at = now() WHERE id = %s::uuid",
                [job_id],
            )

    async def mark_failed(self, job_id) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE jobs SET status = 'failed', finished_at = now() WHERE id = %s::uuid",
                [job_id],
            )

    async def increment_attempt(self, job_id) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE jobs SET attempt = attempt + 1 WHERE id = %s::uuid",
                [job_id],
            )

    async def get_pending(self) -> list[Job]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                "SELECT * FROM jobs WHERE status = 'pending' ORDER BY queued_at",
            )
        return [self._job_from_row(r) for r in rows]

    async def get_stale_jobs(self) -> list[Job]:
        """Return jobs stuck in 'processing' for more than STALE_AFTER minutes."""
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                """
                SELECT * FROM jobs
                WHERE status = 'processing'
                  AND started_at < now() - interval '10 minutes'
                ORDER BY started_at
                """,
            )
        return [self._job_from_row(r) for r in rows]
