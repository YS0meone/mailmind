import { useState } from "react";
import { ReplyEmail } from "@/types";

interface UseMailReplyProps {
  sendReply: (messageID: string, replyData: ReplyEmail) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}
export function useMailReply(): UseMailReplyProps {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendReply = async (messageID: string, replyData: ReplyEmail) => {
    setIsLoading(true);
    setError(null);

    try {
      const rawBaseUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://localhost:8000";
      // Normalize in case env includes a trailing slash or '/api'
      const trimmed = rawBaseUrl.replace(/\/+$/, "");
      const baseUrl = trimmed.replace(/\/api$/, "");
      const url = `${baseUrl}/mail/thread/${messageID}/reply`;
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(replyData),
      });

      if (!response.ok) {
        let message = "Failed to send reply";
        try {
          const data = await response.json();
          message = data?.detail || data?.message || JSON.stringify(data);
        } catch {
          try {
            message = await response.text();
          } catch {
            // ignore
          }
        }
        throw new Error(message);
      }

    } catch (error) {
      setError(error instanceof Error ? error.message : "An error occurred");
      throw error;
    } finally {
      setIsLoading(false);
    }

  };

  return { sendReply, isLoading, error };
}