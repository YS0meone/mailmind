from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class Base(DeclarativeBase):
    pass

# Enums
class EmailLabel(str, Enum):
    inbox = "inbox"
    sent = "sent"
    draft = "draft"

class Sensitivity(str, Enum):
    normal = "normal"
    private = "private"
    personal = "personal"
    confidential = "confidential"

class MeetingMessageMethod(str, Enum):
    request = "request"
    reply = "reply"
    cancel = "cancel"
    counter = "counter"
    other = "other"

# SQLAlchemy ORM Models
class DbUser(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    accountId: Mapped[int] = mapped_column()
    accountToken: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    lastDeltaToken: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<DbUser(id={self.id}, accountId={self.accountId}, email={self.email}, lastDeltaToken={self.lastDeltaToken})>"

class DbThread(Base):
    __tablename__ = 'threads'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    lastMessageDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    involvedEmails: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    inboxStatus: Mapped[bool] = mapped_column(Boolean, default=True)
    draftStatus: Mapped[bool] = mapped_column(Boolean, default=False)
    sentStatus: Mapped[bool] = mapped_column(Boolean, default=False)
      # Relationships
    emails = relationship("DbEmail", back_populates="thread")
    
    __table_args__ = (
        Index('ix_threads_involved_emails_gin', 'involvedEmails', postgresql_using='gin'),
        Index('ix_threads_done', 'done'),
        Index('ix_threads_inbox_status', 'inboxStatus'),
        Index('ix_threads_draft_status', 'draftStatus'),
        Index('ix_threads_sent_status', 'sentStatus'),
        Index('ix_threads_last_message_date', 'lastMessageDate'),
    )

class DbEmail(Base):
    __tablename__ = 'emails'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    threadId: Mapped[str] = mapped_column(String, ForeignKey('threads.id'), nullable=False)
    createdTime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lastModifiedTime: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sentAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    receivedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    internetMessageId: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    sysLabels: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    sysClassifications: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    sensitivity: Mapped[Sensitivity] = mapped_column(String, default=Sensitivity.normal)
    meetingMessageMethod: Mapped[Optional[MeetingMessageMethod]] = mapped_column(String, nullable=True)
    fromAddr: Mapped[str] = mapped_column(String,  nullable=False)
    toAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    ccAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    bccAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    replyToAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    hasAttachments: Mapped[bool] = mapped_column(Boolean, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bodySnippet: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    inReplyTo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    references: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    threadIndex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    internetHeaders: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    nativeProperties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    folderId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    weblink: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    omitted: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    emailLabel: Mapped[EmailLabel] = mapped_column(String, default=EmailLabel.inbox)
    
    # Relationships
    thread = relationship("DbThread", back_populates="emails")
    
    __table_args__ = (
        Index('ix_emails_thread_id', 'threadId'),
        Index('ix_emails_email_label', 'emailLabel'),
        Index('ix_emails_sent_at', 'sentAt'),
    )

# Pydantic Models
class User(BaseModel):
    id: Optional[int] = None  # Auto-generated, so optional for creation
    accountId: int
    accountToken: str
    email: str
    lastDeltaToken: Optional[str] = None

    def __repr__(self):
        return f"User(accountId={self.accountId}, email={self.email}, lastDeltaToken={self.lastDeltaToken})"

class Email(BaseModel):
    id: str
    threadId: str
    createdTime: datetime
    lastModifiedTime: Optional[datetime] = None
    sentAt: datetime
    receivedAt: datetime
    internetMessageId: str
    subject: str
    sysLabels: List[str]
    keywords: List[str]
    sysClassifications: List[str]
    sensitivity: Sensitivity = Sensitivity.normal
    meetingMessageMethod: Optional[MeetingMessageMethod] = None
    fromAddr: str
    toAddrs: List[str]
    ccAddrs: List[str]
    bccAddrs: List[str]
    replyToAddrs: List[str]
    hasAttachments: bool
    body: Optional[str] = None
    bodySnippet: Optional[str] = None
    inReplyTo: Optional[str] = None
    attachments: List[Dict[str, Any]]  # Match SQLAlchemy type exactly
    references: Optional[str] = None
    threadIndex: Optional[str] = None
    internetHeaders: List[Dict[str, Any]]  # Match SQLAlchemy type exactly
    nativeProperties: Optional[Dict[str, Any]] = None
    folderId: Optional[str] = None
    weblink: Optional[str] = None
    omitted: List[str]
    emailLabel: EmailLabel = EmailLabel.inbox

    def __repr__(self):
        return f"Email(id={self.id}, threadId={self.threadId}, subject={self.subject}, fromAddr={self.fromAddr}, sentAt={self.sentAt})"

class Thread(BaseModel):
    id: str
    subject: str
    lastMessageDate: datetime
    involvedEmails: List[str]
    done: bool = False
    inboxStatus: bool = True
    draftStatus: bool = False
    sentStatus: bool = False
    
    def __repr__(self):
        return f"Thread(id={self.id}, subject={self.subject}, lastMessageDate={self.lastMessageDate}, involvedEmails={self.involvedEmails})"
