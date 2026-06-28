from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    color: Mapped[str] = mapped_column(Text, nullable=False, default="gold")
    verse_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    verse_refs: Mapped[list["CollectionVerseRef"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionVerseRef.id",
    )
    notes: Mapped[list["CollectionNote"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
    )


class CollectionVerseRef(Base):
    __tablename__ = "collection_verse_refs"
    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "verse_ref_id",
            name="uq_collection_verse_refs",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    verse_ref_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("verse_refs.id", ondelete="CASCADE"),
        nullable=False,
    )

    collection: Mapped[Collection] = relationship(back_populates="verse_refs")
    verse_ref: Mapped["VerseRef"] = relationship("VerseRef")


class CollectionNote(Base):
    __tablename__ = "collection_notes"
    __table_args__ = (
        UniqueConstraint("collection_id", "note_id", name="uq_collection_notes"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    note_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
    )

    collection: Mapped[Collection] = relationship(back_populates="notes")
    note: Mapped["Note"] = relationship("Note")
