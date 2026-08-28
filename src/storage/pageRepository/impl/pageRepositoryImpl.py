from models.Page import Page
from models.enum.BookStatus import BookStatus
from storage.connection import Database
from storage.pageRepository.pageRepositoryProvider import PageRepositoryProvider


class PageRepositoryImpl(PageRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _page_from_row(row: dict) -> Page:
        return Page(
            id=str(row["id"]),
            processing_run_id=str(row["processing_run_id"]),
            sequence=row["sequence"],
            text=row["text"],
            sentence_count=row["sentence_count"],
            status=BookStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, page: Page) -> Page:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                INSERT INTO pages (processing_run_id, sequence, text, sentence_count, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                [page.processing_run_id, page.sequence, page.text,
                 page.sentence_count, str(page.status)],
            )
        return self._page_from_row(row)

    async def get_by_id(self, page_id) -> Page | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM pages WHERE id = %s::uuid",
                [page_id],
            )
        return self._page_from_row(row) if row else None

    async def get_by_sequence(self, run_id, sequence) -> Page | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM pages WHERE processing_run_id = %s::uuid AND sequence = %s",
                [run_id, sequence],
            )
        return self._page_from_row(row) if row else None

    async def update_status(self, page_id, status: BookStatus) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE pages SET status = %s, updated_at = now() WHERE id = %s::uuid",
                [str(status), page_id],
            )

    async def count_by_status(self, run_id, status: BookStatus) -> int:
        async with self._db.transaction() as tx:
            count = await tx.fetchval(
                "SELECT count(*) FROM pages WHERE processing_run_id = %s::uuid AND status = %s",
                [run_id, str(status)],
            )
        return count or 0

    async def get_pending_pages(self, run_id) -> list[Page]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                """
                SELECT * FROM pages
                WHERE processing_run_id = %s::uuid AND status = 'pending'
                ORDER BY sequence
                """,
                [run_id],
            )
        return [self._page_from_row(r) for r in rows]
