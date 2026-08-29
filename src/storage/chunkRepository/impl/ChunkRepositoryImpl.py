from models.chunk import Chunk
from models.enum.BookStatus import BookStatus
from storage.chunkRepository.chunkRepositoryProvider import ChunkRepositoryProvider
from storage.connection import Database


class ChunkRepositoryImpl(ChunkRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _chunk_from_row(row: dict) -> Chunk:
        return Chunk(
            id=str(row["id"]),
            page_id=str(row["page_id"]),
            sequence=row["sequence"],
            text=row["text"],
            status=BookStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, chunk: Chunk) -> Chunk:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                INSERT INTO chunks (id, page_id, sequence, text, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                [chunk.id, chunk.page_id, chunk.sequence, chunk.text, str(chunk.status)],
            )
        return self._chunk_from_row(row)

    async def create_many(self, chunks: list[Chunk]) -> list[Chunk]:
        created = []
        async with self._db.transaction() as tx:
            for chunk in chunks:
                row = await tx.fetchone(
                    """
                    INSERT INTO chunks (id, page_id, sequence, text, status)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    [chunk.id, chunk.page_id, chunk.sequence, chunk.text, str(chunk.status)],
                )
                created.append(self._chunk_from_row(row))
        return created

    async def get_by_id(self, chunk_id) -> Chunk | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM chunks WHERE id = %s::uuid",
                [chunk_id],
            )
        return self._chunk_from_row(row) if row else None

    async def get_by_page(self, page_id) -> list[Chunk]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                "SELECT * FROM chunks WHERE page_id = %s::uuid ORDER BY sequence",
                [page_id],
            )
        return [self._chunk_from_row(r) for r in rows]

    async def update_status(self, chunk_id, status: BookStatus) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE chunks SET status = %s, updated_at = now() WHERE id = %s::uuid",
                [str(status), chunk_id],
            )

    async def get_pending(self, page_id) -> list[Chunk]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                """
                SELECT * FROM chunks
                WHERE page_id = %s::uuid AND status = 'pending'
                ORDER BY sequence
                """,
                [page_id],
            )
        return [self._chunk_from_row(r) for r in rows]

    async def get_pending_by_run(self, run_id) -> list[Chunk]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                """
                SELECT c.*
                FROM chunks c
                JOIN pages p ON p.id = c.page_id
                WHERE p.processing_run_id = %s::uuid AND c.status = 'pending'
                ORDER BY p.sequence, c.sequence
                """,
                [run_id],
            )
        return [self._chunk_from_row(r) for r in rows]

    async def count_by_status(self, page_id, status: BookStatus) -> int:
        async with self._db.transaction() as tx:
            count = await tx.fetchval(
                "SELECT count(*) FROM chunks WHERE page_id = %s::uuid AND status = %s",
                [page_id, str(status)],
            )
        return count or 0
