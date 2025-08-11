from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, Text, Table, Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Base(DeclarativeBase):
    pass


class EmailLabel(str, Enum):
    inbox = "inbox"
    sent = "sent"
    draft = "draft"
    promotions = "promotions"
    personal = "personal"
    social = "social"
    updates = "updates"
    forums = "forums"
    spam = "spam"
    trash = "trash"


class DbUser(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    accountId: Mapped[int] = mapped_column()
    accountToken: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    lastDeltaToken: Mapped[Optional[str]] = mapped_column(nullable=True)
    passwordHash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    syncDaysWithin: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True)

    def __repr__(self):
        return f"<DbUser(id={self.id}, accountId={self.accountId}, email={self.email}, lastDeltaToken={self.lastDeltaToken})>"


class DbEmailAddress(Base):
    __tablename__ = 'email_addresses'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self):
        return f"<DbEmailAddress(id={self.id}, address={self.address}, name={self.name})>"


email_to_addresses = Table(
    'email_to_addresses',
    Base.metadata,
    Column('email_id', BigInteger, ForeignKey('emails.id'), primary_key=True),
    Column('address_id', Integer, ForeignKey(
        'email_addresses.id'), primary_key=True)
)

email_cc_addresses = Table(
    'email_cc_addresses',
    Base.metadata,
    Column('email_id', BigInteger, ForeignKey('emails.id'), primary_key=True),
    Column('address_id', Integer, ForeignKey(
        'email_addresses.id'), primary_key=True)
)

email_bcc_addresses = Table(
    'email_bcc_addresses',
    Base.metadata,
    Column('email_id', BigInteger, ForeignKey('emails.id'), primary_key=True),
    Column('address_id', Integer, ForeignKey(
        'email_addresses.id'), primary_key=True)
)

email_reply_to_addresses = Table(
    'email_reply_to_addresses',
    Base.metadata,
    Column('email_id', BigInteger, ForeignKey('emails.id'), primary_key=True),
    Column('address_id', Integer, ForeignKey(
        'email_addresses.id'), primary_key=True)
)

address_has_threads = Table(
    'address_has_threads',
    Base.metadata,
    Column('address_id', Integer, ForeignKey(
        'email_addresses.id'), primary_key=True),
    Column('thread_id', BigInteger, ForeignKey('threads.id'), primary_key=True)
)


class DbThread(Base):
    __tablename__ = 'threads'
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True)  # Changed to BigInteger
    subject: Mapped[str] = mapped_column(String, nullable=False)
    lastMessageDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # involvedEmails: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    brief: Mapped[str] = mapped_column(
        String, nullable=False, default="Default Brief")
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    inboxStatus: Mapped[bool] = mapped_column(Boolean, default=True)
    draftStatus: Mapped[bool] = mapped_column(Boolean, default=False)
    sentStatus: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    emails = relationship("DbEmail", back_populates="thread")
    addresses_with_access = relationship(
        "DbEmailAddress",
        secondary=address_has_threads,
        lazy="selectin")

    __table_args__ = (
        # Index('ix_threads_involved_emails_gin', 'involvedEmails', postgresql_using='gin'),
        Index('ix_threads_done', 'done'),
        Index('ix_threads_inbox_status', 'inboxStatus'),
        Index('ix_threads_draft_status', 'draftStatus'),
        Index('ix_threads_sent_status', 'sentStatus'),
        Index('ix_threads_last_message_date', 'lastMessageDate'),
    )


class DbEmail(Base):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True)  # Changed to BigInteger
    threadId: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        'threads.id'), nullable=False)  # Changed to BigInteger
    createdTime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lastModifiedTime: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sentAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    receivedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    labels: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    fromId: Mapped[int] = mapped_column(
        Integer, ForeignKey('email_addresses.id'), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inReplyTo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    emailLabel: Mapped[EmailLabel] = mapped_column(
        String, default=EmailLabel.inbox)
    threadIndex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Relationships
    thread = relationship("DbThread", back_populates="emails")
    from_address = relationship(
        "DbEmailAddress",
        foreign_keys=[fromId],
        lazy="selectin",
    )
    to_addresses = relationship(
        "DbEmailAddress",
        secondary=email_to_addresses,
        lazy="selectin"
    )
    cc_addresses = relationship(
        "DbEmailAddress",
        secondary=email_cc_addresses,
        lazy="selectin"
    )
    bcc_addresses = relationship(
        "DbEmailAddress",
        secondary=email_bcc_addresses,
        lazy="selectin"
    )
    reply_to_addresses = relationship(
        "DbEmailAddress",
        secondary=email_reply_to_addresses,
        lazy="selectin"
    )

    __table_args__ = (
        Index('ix_emails_thread_id', 'threadId'),
        Index('ix_emails_email_label', 'emailLabel'),
        Index('ix_emails_sent_at', 'sentAt'),
    )

    # might be useful in the future
    # internetMessageId: Mapped[str] = mapped_column(String, nullable=False)
    # toAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # ccAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # bccAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # replyToAddrs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # hasAttachments: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # bodySnippet: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # internetHeaders: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    # nativeProperties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    # folderId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # weblink: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # omitted: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # sysClassifications: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    # sensitivity: Mapped[Sensitivity] = mapped_column(String, default=Sensitivity.normal)
    # meetingMessageMethod: Mapped[Optional[MeetingMessageMethod]] = mapped_column(String, nullable=True)
    # attachments: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    # references: Mapped[Optional[str]] = mapped_column(String, nullable=True)


# Pydantic Models
class User(BaseModel):
    id: Optional[int] = None  # Auto-generated, so optional for creation
    accountId: int
    accountToken: str
    email: str
    lastDeltaToken: Optional[str] = None

    def __repr__(self):
        return f"User(accountId={self.accountId}, email={self.email}, lastDeltaToken={self.lastDeltaToken})"


class EmailAddress(BaseModel):
    id: Optional[int] = None
    address: str
    name: Optional[str] = None

    def __repr__(self):
        return f"EmailAddress(address={self.address}, name={self.name})"


class Thread(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    lastMessageDate: datetime
    done: bool = False
    brief: str
    inboxStatus: bool = True
    draftStatus: bool = False
    sentStatus: bool = False
    emails: List['Email'] = []

    def __repr__(self):
        return f"Thread(id={self.id}, subject={self.subject}, lastMessageDate={self.lastMessageDate}, done={self.done})"

    @field_validator("id", mode="before")
    @classmethod
    def _hex_to_id(cls, v):
        if isinstance(v, str):
            s = v.strip().lower()
            if s.startswith("0x"):
                s = s[2:]
            if not s or any([b for b in s.encode() if b not in range(ord('0'), ord('9'))]):
                raise ValueError("Invalid hex string")
            return int(s, 16)
        if isinstance(v, int):
            return v
        raise ValueError("Invalid id")

    @field_serializer("id")
    def _id_to_str(self, v, _):
        return format(v, 'x')


class Email(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    threadId: int
    createdTime: datetime
    lastModifiedTime: Optional[datetime] = None
    sentAt: datetime
    receivedAt: datetime
    subject: str
    labels: List[str] = []
    fromId: int
    body: Optional[str] = None
    inReplyTo: Optional[str] = None
    emailLabel: EmailLabel = EmailLabel.inbox
    threadIndex: Optional[str] = None
    from_address: Optional[EmailAddress] = None
    to_addresses: List[EmailAddress] = []
    cc_addresses: List[EmailAddress] = []
    bcc_addresses: List[EmailAddress] = []
    reply_to_addresses: List[EmailAddress] = []

    def __repr__(self):
        return f"Email(id={self.id}, threadId={self.threadId}, subject={self.subject}, fromId={self.fromId}, sentAt={self.sentAt})"

    @field_validator("id", mode="before")
    @classmethod
    def _hex_to_id(cls, v):
        if isinstance(v, str):
            s = v.strip().lower()
            if s.startswith("0x"):
                s = s[2:]
            if not s or any([b for b in s.encode() if b not in range(ord('0'), ord('9'))]):
                raise ValueError("Invalid hex string")
            return int(s, 16)
        if isinstance(v, int):
            return v
        raise ValueError("Invalid id")

    @field_serializer("id")
    def _id_to_hex(self, v, _):
        return format(v, 'x')


class ReplyEmail(BaseModel):
    from_address: EmailAddress
    subject: str
    body: str
    to: List[EmailAddress]
    cc: List[EmailAddress]
    bcc: List[EmailAddress]

    def __repr__(self):
        return f"ReplyEmail(subject={self.subject}, from_address={self.from_address}, to={self.to}, cc={self.cc}, bcc={self.bcc}, body={self.body})"


# Update forward references for Pydantic models
Thread.model_rebuild()
