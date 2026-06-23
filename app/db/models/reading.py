from sqlalchemy import CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReadingPosition(Base):
    __tablename__ = "reading_position"
    __table_args__ = (CheckConstraint("id = 1", name="reading_position_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    chapter: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    verse: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class BookProgress(Base):
    __tablename__ = "book_progress"
    __table_args__ = (
        CheckConstraint("percent >= 0 AND percent <= 100", name="book_progress_percent"),
    )

    book_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_chapter: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_verse: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
