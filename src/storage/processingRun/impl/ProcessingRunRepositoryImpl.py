from models.ProcessingRun import ProcessingRun
from models.enum.BookStatus import BookStatus
from storage.connection import Database
from storage.processingRun.processingRunRepositoryProvider import ProcessingRunRepositoryProvider


class ProcessingRunRepositoryImpl(ProcessingRunRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _run_from_row(row: dict) -> ProcessingRun:
        return ProcessingRun(
            id=str(row["id"]),
            book_id=str(row["book_id"]),
            status=BookStatus(row["status"]),
            page_size=row["page_size"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    async def create(self, book_id, page_size: int = 0) -> ProcessingRun:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                INSERT INTO processing_runs (book_id, status, page_size)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                [book_id, str(BookStatus.PENDING), page_size],
            )
        return self._run_from_row(row)

    async def get_by_id(self, run_id) -> ProcessingRun | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM processing_runs WHERE id = %s::uuid",
                [run_id],
            )
        return self._run_from_row(row) if row else None

    async def update_status(self, run_id, status: BookStatus) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE processing_runs SET status = %s WHERE id = %s::uuid",
                [str(status), run_id],
            )

    async def finish(self, run_id) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                """
                UPDATE processing_runs
                SET status = 'completed', completed_at = now()
                WHERE id = %s::uuid
                """,
                [run_id],
            )
