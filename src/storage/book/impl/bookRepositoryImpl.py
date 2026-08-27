from models.Book import Book
from models.enum.BookStatus import BookStatus
from storage.book.bookRepositoryProvider import BookRepositoryProvider
from storage.connection import Database


class BookRepositoryImpl(BookRepositoryProvider):

    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _book_from_row(row: dict) -> Book:
        row["id"] = str(row["id"])
        return Book(**row)

    async def create(self, book: Book) -> Book:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                """
                INSERT INTO books (title, author, language, status, book_url,
                                   total_pages, completed_pages)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                [book.title, book.author, str(book.language), str(book.status),
                 book.book_url, book.total_pages, book.completed_pages],
            )
        return self._book_from_row(row)

    async def get_by_id(self, book_id: str) -> Book | None:
        async with self._db.transaction() as tx:
            row = await tx.fetchone(
                "SELECT * FROM books WHERE id = %s::uuid",
                [book_id],
            )
        return self._book_from_row(row) if row else None

    async def update_status(self, book_id: str, status: BookStatus) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                "UPDATE books SET status = %s, updated_at = now() WHERE id = %s::uuid",
                [str(status), book_id],
            )

    async def increment_completed_pages(self, book_id: str) -> None:
        async with self._db.transaction() as tx:
            await tx.execute(
                """
                UPDATE books
                SET completed_pages = completed_pages + 1, updated_at = now()
                WHERE id = %s::uuid
                """,
                [book_id],
            )

    async def get_progress(self, book_id: str) -> int:
        async with self._db.transaction() as tx:
            completed = await tx.fetchval(
                "SELECT completed_pages FROM books WHERE id = %s::uuid",
                [book_id],
            )
        return completed or 0
