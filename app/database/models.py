"""
Database models.

Simplified single-group design:
- No per-mahalla Telegram groups. Every appeal goes to ONE group (GROUP_ID).
- Mahalla is stored as plain text (chosen from app/constants.py MAHALLA_LIST)
  purely for record-keeping / statistics, not for routing.
- Appeal supports one optional attached media file (photo / video / voice /
  document), stored by Telegram file_id (Telegram hosts the actual file).
"""

import enum

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class AppealType(str, enum.Enum):
    COMPLAINT = "complaint"        # Shikoyat
    APPLICATION = "application"    # Ariza
    SUGGESTION = "suggestion"      # Taklif
    GRATITUDE = "gratitude"        # Minnatdorchilik
    EMERGENCY = "emergency"        # Shoshilinch


class AppealStatus(str, enum.Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    NEED_INFO = "need_info"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CLOSED = "closed"


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    VOICE = "voice"
    DOCUMENT = "document"


class Citizen(Base, AuditMixin):
    """A Telegram user who has interacted with the bot."""

    __tablename__ = "citizens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="uz", nullable=False)

    mahalla_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    street_and_house: Mapped[str | None] = mapped_column(String(255), nullable=True)

    appeals: Mapped[list["Appeal"]] = relationship(back_populates="citizen")

    def __repr__(self) -> str:
        return f"<Citizen id={self.id} full_name={self.full_name!r}>"


class Appeal(Base, AuditMixin):
    """A single citizen appeal (complaint / suggestion / etc.)."""

    __tablename__ = "appeals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tracking_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)

    citizen_id: Mapped[int] = mapped_column(ForeignKey("citizens.id"), nullable=False)

    appeal_type: Mapped[AppealType] = mapped_column(
        String(20), default=AppealType.COMPLAINT, nullable=False
    )
    status: Mapped[AppealStatus] = mapped_column(
        String(20), default=AppealStatus.NEW, nullable=False, index=True
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mahalla_name: Mapped[str] = mapped_column(String(120), nullable=False)
    street_and_house: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional attached media - Telegram stores the actual file, we only
    # keep its file_id + type so it can be re-sent/forwarded any time.
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    media_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Telegram message id of the card posted in the group, so the bot can
    # edit it in place when the status changes.
    group_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    citizen: Mapped["Citizen"] = relationship(back_populates="appeals")
    status_history: Mapped[list["AppealStatusHistory"]] = relationship(
        back_populates="appeal", order_by="AppealStatusHistory.id"
    )

    def __repr__(self) -> str:
        return f"<Appeal {self.tracking_number} status={self.status}>"


class AppealStatusHistory(Base, AuditMixin):
    """Audit trail: every status change of an appeal, who changed it and when."""

    __tablename__ = "appeal_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appeal_id: Mapped[int] = mapped_column(ForeignKey("appeals.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    appeal: Mapped["Appeal"] = relationship(back_populates="status_history")
