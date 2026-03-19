"""수집 도메인 SQLModel 모델.

Table Structure:
- CollectionSetting: 수집 설정 (브랜드×카테고리 매핑)
- CollectionLog: 수집 로그
- ExtensionCommand: 익스텐션 명령 큐
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Index, func


class CommandTypeEnum(str, Enum):
    """익스텐션 명령 타입"""
    MONITOR_REGISTER = "monitor_register"
    MONITOR_UNREGISTER = "monitor_unregister"


class CommandStatusEnum(str, Enum):
    """명령 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class LogStatusEnum(str, Enum):
    """수집 로그 상태"""
    SUCCESS = "success"
    FAILED = "failed"


class CollectionSetting(SQLModel, table=True):
    """수집 설정 — 브랜드×카테고리 매핑"""
    __tablename__ = "collection_settings"
    __table_args__ = (
        Index("ix_collection_settings_source_id", "source_id"),
        Index("ix_collection_settings_is_active", "is_active"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(200), nullable=False))
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    brand_name: str = Field(sa_column=Column(String(200), nullable=False))
    category_url: str = Field(sa_column=Column(Text, nullable=False))
    max_count: int = Field(
        default=500,
        sa_column=Column(Integer, nullable=False, server_default="500"),
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )
    last_collected_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    collected_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )


class CollectionLog(SQLModel, table=True):
    """수집 로그"""
    __tablename__ = "collection_logs"
    __table_args__ = (
        Index("ix_collection_logs_created_at", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    setting_id: Optional[int] = Field(
        default=None, foreign_key="collection_settings.id", nullable=True,
    )
    product_name: str = Field(sa_column=Column(String(500), nullable=False))
    status: LogStatusEnum = Field(sa_column=Column(String(20), nullable=False))
    message: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ExtensionCommand(SQLModel, table=True):
    """익스텐션 명령 큐"""
    __tablename__ = "extension_commands"
    __table_args__ = (
        Index("ix_extension_commands_status", "status"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    command_type: CommandTypeEnum = Field(sa_column=Column(String(50), nullable=False))
    payload: str = Field(sa_column=Column(Text, nullable=False))
    status: CommandStatusEnum = Field(
        default=CommandStatusEnum.PENDING,
        sa_column=Column(String(20), nullable=False, server_default="pending"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
