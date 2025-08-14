import { Thread } from "@/types";
import MessageDisplay from "./ui/message-display";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function ThreadDisplay({ thread }: { thread: Thread | null }) {
  if (!thread) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        No thread selected
      </div>
    );
  }

  return (
    <ScrollArea className="h-full pr-2">
      {thread.emails.map((email) => (
        <MessageDisplay key={email.id} email={email} />
      ))}
    </ScrollArea>
  );
}
