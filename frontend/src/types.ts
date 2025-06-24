export interface DbEmail {
  id: string;
  threadId: string;
  createdTime: string;
  lastModifiedTime?: string;
  sentAt: string;
  receivedAt: string;
  internetMessageId: string;
  subject: string;
  sysLabels: string[];
  keywords: string[];
  sysClassifications: string[];
  sensitivity: string;
  meetingMessageMethod?: string;
  fromAddr: string;
  toAddrs: string[];
  ccAddrs: string[];
  bccAddrs: string[];
  replyToAddrs: string[];
  hasAttachments: boolean;
  body?: string;
  bodySnippet?: string;
  inReplyTo?: string;
  attachments: Array<Record<string, any>>;
  references?: string;
  threadIndex?: string;
  internetHeaders: Array<Record<string, any>>;
  nativeProperties?: Record<string, any>;
  folderId?: string;
  weblink?: string;
  omitted: string[];
  emailLabel: string;
}

export interface Mail {
  id: string;
  name: string;
  email: string;
  subject: string;
  text: string;
  date: string;
  read: boolean;
  labels: string[];
}

export interface Thread {
  id: string;
  subject: string;
  lastMessageDate: string;
  involvedEmails: string[];
  done: boolean;
  inboxStatus: boolean;
  draftStatus: boolean;
  sentStatus: boolean;
}
