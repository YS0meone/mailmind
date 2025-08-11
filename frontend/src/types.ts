export interface DbAddress {
  id: number;
  address: string;
  name?: string;
}

export interface DbEmail {
  id: string;
  threadId: number;
  createdTime: string;
  lastModifiedTime?: string;
  sentAt: string;
  receivedAt: string;
  subject: string;
  labels: string[];
  fromId: number;
  body?: string;
  inReplyTo?: string;
  emailLabel: string;
  threadIndex?: string;
  from_address: DbAddress;
  to_addresses: DbAddress[];
  cc_addresses: DbAddress[];
  bcc_addresses: DbAddress[];
  reply_to_addresses: DbAddress[];
}

// export interface Mail {
//   id: string;
//   name: string;
//   email: string;
//   subject: string;
//   text: string;
//   date: string;
//   read: boolean;
//   labels: string[];
// }

export interface Thread {
  id: string;
  subject: string;
  lastMessageDate: string;
  brief: string;
  done: boolean;
  inboxStatus: boolean;
  draftStatus: boolean;
  sentStatus: boolean;
  emails: DbEmail[];
}

export interface ReplyEmail {
  from_address: DbAddress;
  subject: string;
  body: string;
  to: DbAddress[];
  cc: DbAddress[];
  bcc: DbAddress[];
}