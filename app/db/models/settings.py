from sqlalchemy import CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

DEFAULT_BIBLE_VERSION_ID = 4


class AppSettings(Base):
    __tablename__ = "app_settings"
    __table_args__ = (CheckConstraint("id = 1", name="app_settings_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bible_version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=DEFAULT_BIBLE_VERSION_ID
    )
