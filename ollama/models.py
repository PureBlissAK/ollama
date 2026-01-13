"""
Ollama Database Models - SQLAlchemy ORM
Provides data models for users, conversations, messages, and metadata
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User account model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    api_key_hash = Column(String(255), nullable=True)
    preferences = Column(JSONB, default={}, nullable=False)
    user_metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_user_created", "created_at"),
        Index("ix_user_active", "is_active"),
    )


class APIKey(Base):
    """API Key model for programmatic access"""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    scopes = Column(JSON, default=[], nullable=False)
    rate_limit = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    apikey_metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_key_user", "user_id"),
        Index("ix_api_key_active", "is_active"),
    )


class Conversation(Base):
    """Conversation model - represents a chat session"""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    model = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    parameters = Column(JSONB, default={}, nullable=False)
    is_archived = Column(Boolean, default=False, index=True)
    is_favorite = Column(Boolean, default=False)
    tags = Column(JSON, default=[], nullable=False)
    conv_metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conv_user", "user_id"),
        Index("ix_conv_model", "model"),
        Index("ix_conv_archived", "is_archived"),
        Index("ix_conv_created", "created_at"),
    )


class Message(Base):
    """Message model - represents a single turn in a conversation"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    finish_reason = Column(String(50), nullable=True)
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(255), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    msg_metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_msg_conversation", "conversation_id"),
        Index("ix_msg_role", "role"),
        Index("ix_msg_created", "created_at"),
    )


class Document(Base):
    """Document model - for RAG (Retrieval Augmented Generation)"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    chunks = Column(JSON, default=[], nullable=False)
    vector_collection = Column(String(255), nullable=True)
    is_indexed = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False)
    tags = Column(JSON, default=[], nullable=False)
    doc_metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_doc_user", "user_id"),
        Index("ix_doc_indexed", "is_indexed"),
        Index("ix_doc_created", "created_at"),
    )


class Usage(Base):
    """Usage tracking model for monitoring and analytics"""

    __tablename__ = "usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    model = Column(String(255), nullable=True)
    method = Column(String(10), nullable=False)
    response_time_ms = Column(Float, nullable=False)
    status_code = Column(Integer, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    usage_metadata = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_usage_user", "user_id"),
        Index("ix_usage_endpoint", "endpoint"),
        Index("ix_usage_created", "created_at"),
    )


# Event listeners for automatic timestamp updates
@event.listens_for(User, "before_update")
def receive_before_update_user(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(APIKey, "before_update")
def receive_before_update_apikey(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(Conversation, "before_update")
def receive_before_update_conversation(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(Message, "before_update")
def receive_before_update_message(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(Document, "before_update")
def receive_before_update_document(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
