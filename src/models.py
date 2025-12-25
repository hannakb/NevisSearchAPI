import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_id("client"),
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_id("document"),
    )
    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    embedding = mapped_column(Vector(384), nullable=True)

    client: Mapped["Client"] = relationship(back_populates="documents")
