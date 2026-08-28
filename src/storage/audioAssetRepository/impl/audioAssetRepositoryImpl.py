from models.AudioAsset import AudioAsset
from models.chunk import Chunk
from models.enum.BookStatus import BookStatus
from storage.audioAssetRepository.audioAssetRepositoryProvider import AudioAssetRepositoryProvider
from storage.connection import Database


class AudioAssetRepositoryImpl(AudioAssetRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _audio_asset_from_row(row: dict) -> AudioAsset:
        return AudioAsset(
            id=str(row["id"]),
            chunk_id=str(row["chunk_id"]),
            storage_key=row["storage_key"],
            format=row["format"],
            duration=row["duration"],
            size=row["size"],
            status=BookStatus(row["status"]),
            created_at=row["created_at"],
        )

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

    async def create(self, audio_asset: AudioAsset) -> AudioAsset:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                INSERT INTO audio_assets (chunk_id, storage_key, format, duration, size, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                [audio_asset.chunk_id, audio_asset.storage_key, audio_asset.format,
                 audio_asset.duration, audio_asset.size, str(audio_asset.status)],
            )
        return self._audio_asset_from_row(row)

    async def get_by_id(self, audio_asset_id) -> AudioAsset | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM audio_assets WHERE id = %s::uuid",
                [audio_asset_id],
            )
        return self._audio_asset_from_row(row) if row else None

    async def get_by_chunk(self, chunk_id) -> AudioAsset | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM audio_assets WHERE chunk_id = %s::uuid",
                [chunk_id],
            )
        return self._audio_asset_from_row(row) if row else None

    async def get_next_job(self) -> Chunk | None:
        """Return the next pending chunk that has no audio asset yet.

        The audio job queue is driven by chunks: a chunk is a "job" while it
        has no generated asset. We left-join audio_assets so a chunk with an
        existing asset (any status) is never picked again.
        """
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                SELECT c.*
                FROM chunks c
                LEFT JOIN audio_assets a ON a.chunk_id = c.id
                WHERE c.status = 'pending' AND a.id IS NULL
                ORDER BY c.created_at
                LIMIT 1
                """,
            )
        return self._chunk_from_row(row) if row else None

    async def get_by_page(self, page_id) -> list[AudioAsset]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                """
                SELECT a.*
                FROM audio_assets a
                JOIN chunks c ON c.id = a.chunk_id
                WHERE c.page_id = %s::uuid
                ORDER BY c.sequence
                """,
                [page_id],
            )
        return [self._audio_asset_from_row(r) for r in rows]

    async def update_status(self, audio_asset_id, status: BookStatus) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE audio_assets SET status = %s WHERE id = %s::uuid",
                [str(status), audio_asset_id],
            )
