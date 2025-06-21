from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
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
    lastDeltaToken: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<DbUser(id={self.id}, accountId={self.accountId}, email={self.email}, lastDeltaToken={self.lastDeltaToken})>"

class DbAccount(Base):
    __tablename__ = 'accounts'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Relationships
    threads = relationship("DbThread", back_populates="account")
    emailAddresses = relationship("DbEmailAddress", back_populates="account")

class DbThread(Base):
    __tablename__ = 'threads'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    lastMessageDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    participantIds: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    accountId: Mapped[str] = mapped_column(String, ForeignKey('accounts.id'), nullable=False)
    
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    inboxStatus: Mapped[bool] = mapped_column(Boolean, default=True)
    draftStatus: Mapped[bool] = mapped_column(Boolean, default=False)
    sentStatus: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    account = relationship("DbAccount", back_populates="threads")
    emails = relationship("DbEmail", back_populates="thread")
    
    __table_args__ = (
        Index('ix_threads_accountId', 'accountId'),
        Index('ix_threads_done', 'done'),
        Index('ix_threads_inbox_status', 'inboxStatus'),
        Index('ix_threads_draft_status', 'draftStatus'),
        Index('ix_threads_sent_status', 'sentStatus'),
        Index('ix_threads_last_message_date', 'lastMessageDate'),
    )

class DbEmailAddress(Base):
    __tablename__ = 'email_addresses'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=False)
    raw: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    accountId: Mapped[str] = mapped_column(String, ForeignKey('accounts.id'), nullable=False)
    
    # Relationships
    account = relationship("DbAccount", back_populates="emailAddresses")
    sentEmails = relationship("DbEmail", foreign_keys="DbEmail.fromId", back_populates="fromAddress")
    
    __table_args__ = (
        Index('ix_email_addresses_account_address', 'accountId', 'address', unique=True),
    )

class DbEmail(Base):
    __tablename__ = 'emails'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    threadId: Mapped[str] = mapped_column(String, ForeignKey('threads.id'), nullable=False)
    createdTime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lastModifiedTime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sentAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    receivedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    internetMessageId: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    sysLabels: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    sysClassifications: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    sensitivity: Mapped[Sensitivity] = mapped_column(String, default=Sensitivity.normal)
    meetingMessageMethod: Mapped[Optional[MeetingMessageMethod]] = mapped_column(String, nullable=True)
    fromId: Mapped[str] = mapped_column(String, ForeignKey('email_addresses.id'), nullable=False)
    hasAttachments: Mapped[bool] = mapped_column(Boolean, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bodySnippet: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    inReplyTo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    references: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    threadIndex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    internetHeaders: Mapped[List[dict]] = mapped_column(JSON, nullable=False)
    nativeProperties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    folderId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    weblink: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    omitted: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    emailLabel: Mapped[EmailLabel] = mapped_column(String, default=EmailLabel.inbox)
    
    # Relationships
    thread = relationship("DbThread", back_populates="emails")
    fromAddress = relationship("DbEmailAddress", foreign_keys=[fromId], back_populates="sentEmails")
    attachments = relationship("DbEmailAttachment", back_populates="email")
    
    __table_args__ = (
        Index('ix_emails_thread_id', 'threadId'),
        Index('ix_emails_email_label', 'emailLabel'),
        Index('ix_emails_sent_at', 'sentAt'),
    )

class DbEmailAttachment(Base):
    __tablename__ = 'email_attachments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    mimeType: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    inline: Mapped[bool] = mapped_column(Boolean, nullable=False)
    contentId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contentLocation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    emailId: Mapped[str] = mapped_column(String, ForeignKey('emails.id'), nullable=False)
    
    # Relationships
    email = relationship("DbEmail", back_populates="attachments")

# Pydantic Models
class User(BaseModel):
    accountId: int
    accountToken: str
    lastDeltaToken: str | None = None
    email: str

    def __repr__(self):
        return f"User(accountId={self.accountId}, email={self.email}, lastDeltaToken={self.lastDeltaToken})"

class Account(BaseModel):
    id: str

class EmailAddress(BaseModel):
    id: str
    name: Optional[str] = None
    address: str
    raw: Optional[str] = None
    accountId: str

class EmailAttachment(BaseModel):
    id: str
    name: str
    mimeType: str
    size: int
    inline: bool
    contentId: Optional[str] = None
    content: Optional[str] = None
    contentLocation: Optional[str] = None
    emailId: str

class Email(BaseModel):
    id: str
    threadId: str
    createdTime: datetime
    lastModifiedTime: datetime
    sentAt: datetime
    receivedAt: datetime
    internetMessageId: str
    subject: str
    sysLabels: List[str]
    keywords: List[str]
    sysClassifications: List[str]
    sensitivity: Sensitivity = Sensitivity.normal
    meetingMessageMethod: Optional[MeetingMessageMethod] = None
    fromId: str
    hasAttachments: bool
    body: Optional[str] = None
    bodySnippet: Optional[str] = None
    inReplyTo: Optional[str] = None
    references: Optional[str] = None
    threadIndex: Optional[str] = None
    internetHeaders: List[dict]
    nativeProperties: Optional[dict] = None
    folderId: Optional[str] = None
    omitted: List[str]
    weblink: Optional[str] = None
    emailLabel: EmailLabel = EmailLabel.inbox
    
    # Related objects
    fromAddress: Optional[EmailAddress] = None
    toAddresses: List[EmailAddress] = []
    ccAddresses: List[EmailAddress] = []
    bccAddresses: List[EmailAddress] = []
    replyToAddresses: List[EmailAddress] = []
    attachments: List[EmailAttachment] = []

class Thread(BaseModel):
    id: str
    subject: str
    lastMessageDate: datetime
    participantIds: List[str]
    accountId: str
    done: bool = False
    inboxStatus: bool = True
    draftStatus: bool = False
    sentStatus: bool = False
    
    # Related objects
    emails: List[Email] = []
