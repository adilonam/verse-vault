from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BibleVersionKey(Base):
    __tablename__ = "bible_version_key"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table: Mapped[str] = mapped_column("table", Text, nullable=False)
    abbreviation: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    info_text: Mapped[str] = mapped_column(Text, nullable=False)
    info_url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(Text, nullable=False)
    copyright: Mapped[str] = mapped_column(Text, nullable=False)
    copyright_info: Mapped[str] = mapped_column(Text, nullable=False)


class KeyEnglish(Base):
    __tablename__ = "key_english"

    b: Mapped[int] = mapped_column(Integer, primary_key=True)
    n: Mapped[str] = mapped_column(Text, nullable=False)


class VerseMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    b: Mapped[int] = mapped_column(Integer, nullable=False)
    c: Mapped[int] = mapped_column(Integer, nullable=False)
    v: Mapped[int] = mapped_column(Integer, nullable=False)
    t: Mapped[str] = mapped_column(Text, nullable=False)


class TAsv(VerseMixin, Base):
    __tablename__ = "t_asv"


class TBbe(VerseMixin, Base):
    __tablename__ = "t_bbe"


class TDby(VerseMixin, Base):
    __tablename__ = "t_dby"


class TKjv(VerseMixin, Base):
    __tablename__ = "t_kjv"


class TWbt(VerseMixin, Base):
    __tablename__ = "t_wbt"


class TWeb(VerseMixin, Base):
    __tablename__ = "t_web"


class TYlt(VerseMixin, Base):
    __tablename__ = "t_ylt"


VERSE_TABLE_MODELS: dict[str, type[VerseMixin]] = {
    "t_asv": TAsv,
    "t_bbe": TBbe,
    "t_dby": TDby,
    "t_kjv": TKjv,
    "t_wbt": TWbt,
    "t_web": TWeb,
    "t_ylt": TYlt,
}
