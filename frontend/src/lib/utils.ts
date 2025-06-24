import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { DbEmail, Mail } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


export function convertDbEmailToMail(dbEmail: DbEmail): Mail {
  // Extract name from email address (fallback if no display name)
  const extractNameFromEmail = (emailAddr: string): string => {
    if (!emailAddr) return 'Unknown';
    
    // Check if email has display name format: "Name <email@domain.com>"
    const displayNameMatch = emailAddr.match(/^(.+?)\s*<.+>$/);
    if (displayNameMatch) {
      return displayNameMatch[1].trim().replace(/['"]/g, '');
    }
    
    // Otherwise extract name from email address before @
    const localPart = emailAddr.split('@')[0];
    return localPart.split('.').map((part: string) => 
      part.charAt(0).toUpperCase() + part.slice(1)
    ).join(' ');
  };

  // Extract plain email address from potentially formatted string
  const extractEmailAddress = (emailAddr: string): string => {
    if (!emailAddr) return '';
    
    const emailMatch = emailAddr.match(/<(.+?)>$/);
    return emailMatch ? emailMatch[1] : emailAddr;
  };

  // Determine if email is read based on system labels
  const isRead = !dbEmail.sysLabels.includes('UNREAD');

  // Convert keywords and classifications to labels
  const labels = [
    ...dbEmail.keywords,
    ...dbEmail.sysClassifications
  ].filter(Boolean);

  return {
    id: dbEmail.id,
    name: extractNameFromEmail(dbEmail.fromAddr),
    email: extractEmailAddress(dbEmail.fromAddr),
    subject: dbEmail.subject,
    text: dbEmail.body || dbEmail.bodySnippet || '',
    date: dbEmail.sentAt,
    read: isRead,
    labels: labels
  };
}

export function convertDbEmailsToMails(dbEmails: DbEmail[]): Mail[] {
  return dbEmails.map(convertDbEmailToMail);
}