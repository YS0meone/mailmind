import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Button } from "./ui/button";
import { DbEmail, ReplyEmail } from "@/types";
import { useEffect, useState } from "react";
import { useMailReply } from "@/hooks/use-mail-reply";

export default function MailReply({ email }: { email: DbEmail | null }) {
  const [replyEmail, setReplyEmail] = useState<ReplyEmail | null>(null);
  const { sendReply, isLoading, error } = useMailReply();

  useEffect(() => {
    if (email) {
      setReplyEmail({
        from_address: email.to_addresses[0],
        subject: `Re: ${email.subject}`,
        body: "",
        to: [email.from_address],
        cc: [],
        bcc: [],
      });
    } else {
      setReplyEmail(null);
    }
  }, [email]);

  if (!email) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!replyEmail) return;
    try {
      console.log("email id in hex", email.id);
      const response = await sendReply(email.id, replyEmail);
      console.log("Reply sent:", response);
      // Reset form or show success message
      setReplyEmail({
        from_address: email.to_addresses[0],
        subject: `Re: ${email.subject}`,
        body: "",
        to: [email.from_address],
        cc: [],
        bcc: [],
      });
    } catch (error) {
      console.error("Error sending reply:", error);
    }
  };

  return (
    <div className="p-4">
      <form onSubmit={handleSubmit}>
        <div className="grid gap-4">
          <Textarea
            className="p-4"
            placeholder={`Reply to ${
              email.from_address.name || email.from_address.address
            }...`}
            value={replyEmail?.body}
            onChange={(e) =>
              replyEmail &&
              setReplyEmail({ ...replyEmail, body: e.target.value })
            }
          />
          <div className="flex items-center">
            <Label
              htmlFor="mute"
              className="flex items-center gap-2 text-xs font-normal"
            >
              <Switch id="mute" aria-label="Mute thread" /> Mute this thread
            </Label>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button
              type="submit"
              size="sm"
              className="ml-auto"
              disabled={isLoading || !replyEmail?.body?.trim()}
            >
              {isLoading ? "Sending..." : "Send"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
