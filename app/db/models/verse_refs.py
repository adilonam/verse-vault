from sqlalchemy import Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VerseRef(Base):
    __tablename__ = "verse_refs"
    __table_args__ = (
        UniqueConstraint("book_id", "chapter", "verse", name="uq_verse_refs_passage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter: Mapped[int] = mapped_column(Integer, nullable=False)
    verse: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str] = mapped_column(Text, nullable=False)
