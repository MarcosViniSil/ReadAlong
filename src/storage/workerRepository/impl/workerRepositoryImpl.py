from models.WorkerMetric import WorkerMetric
from models.enum.WorkerStatus import WorkerStatus
from models.worker import Worker
from storage.connection import Database
from storage.workerRepository.workerRepositoryProvider import WorkerRepositoryProvider


class WorkerRepositoryImpl(WorkerRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _worker_from_row(row: dict) -> Worker:
        return Worker(
            id=str(row["id"]),
            name=row["name"],
            status=WorkerStatus(row["status"]),
            cpu_model=row["cpu_model"],
            cpu_cores=row["cpu_cores"],
            cpu_threads=row["cpu_threads"],
            ram_total=row["ram_total"],
            ram_type=row["ram_type"],
            ram_speed=row["ram_speed"],
            os=row["os"],
            os_version=row["os_version"],
            last_heart_beat=row["last_heart_beat"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def register(self, worker: Worker) -> Worker:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                INSERT INTO workers (name, status, cpu_model, cpu_cores, cpu_threads,
                                     ram_total, ram_type, ram_speed, os, os_version,
                                     last_heart_beat)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                [worker.name, str(worker.status), worker.cpu_model, worker.cpu_cores,
                 worker.cpu_threads, worker.ram_total, worker.ram_type, worker.ram_speed,
                 worker.os, worker.os_version, worker.last_heart_beat],
            )
        return self._worker_from_row(row)

    async def get_by_id(self, worker_id) -> Worker | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM workers WHERE id = %s::uuid",
                [worker_id],
            )
        return self._worker_from_row(row) if row else None

    async def get_all(self) -> list[Worker]:
        async with self._db.transaction() as tx:
            rows = await tx.fetchall("SELECT * FROM workers ORDER BY name")
        return [self._worker_from_row(r) for r in rows]

    async def update_status(self, worker_id, status: WorkerStatus) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE workers SET status = %s, updated_at = now() WHERE id = %s::uuid",
                [str(status), worker_id],
            )

    async def heartbeat(self, worker_id) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                """
                UPDATE workers
                SET last_heart_beat = now(), updated_at = now()
                WHERE id = %s::uuid
                """,
                [worker_id],
            )

    async def update_metrics(self, metrics: WorkerMetric) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                """
                INSERT INTO worker_metrics (worker_id, cpu_usage, memory_usage,
                                            disk_usage, cpu_temperature)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [metrics.worker_id, metrics.cpu_usage, metrics.memory_usage,
                 metrics.disk_usage, metrics.cpu_temperature],
            )

    async def get_online_workers(self) -> list[Worker]:
        """Return healthy workers with a heartbeat in the last 5 minutes."""
        async with self._db.transaction() as tx:
            rows = await tx.fetchall(
                """
                SELECT * FROM workers
                WHERE status = 'healthy'
                  AND last_heart_beat >= now() - interval '5 minutes'
                ORDER BY last_heart_beat DESC
                """,
            )
        return [self._worker_from_row(r) for r in rows]
