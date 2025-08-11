import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { format } from "date-fns";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { DbEmail } from "@/types";

export default function MessageDisplay({ email }: { email: DbEmail }) {
  console.log(email);
  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-start p-4">
        <div className="flex items-start gap-4 text-sm">
          <Avatar>
            {/* <AvatarImage alt={thread.emails[0].from_address.name ?? "Unknown"} /> */}
            <AvatarFallback>
              {email.from_address.name ? email.from_address.name[0] : "Unknown"}
            </AvatarFallback>
          </Avatar>
          <div className="grid gap-1">
            <div className="font-semibold">
              {email.from_address.name ?? "Unknown"}
            </div>
            <div className="line-clamp-1 text-xs">{email.subject}</div>
            <div className="line-clamp-1 text-xs">
              <span className="font-medium">Reply-To:</span>{" "}
              {email.reply_to_addresses.map((addr) => addr.address).join(", ")}
            </div>
          </div>
        </div>
        {email.lastModifiedTime && (
          <div className="ml-auto text-xs text-muted-foreground">
            {format(new Date(email.lastModifiedTime), "PPpp")}
          </div>
        )}
      </div>
      <Separator />
      <div className="h-full overflow-hidden">
        {email.body ? (
          <div className="h-full p-4">
            <div className="h-full border rounded-md">
              <iframe
                srcDoc={`
                    <!DOCTYPE html>
                    <html>
                      <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <style>
                          body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                            font-size: 14px;
                            line-height: 1.5;
                            color: #333;
                            background: #fff;
                            margin: 12px;
                            word-wrap: break-word;
                            overflow-wrap: break-word;
                          }
                          img { max-width: 100%; height: auto; }
                          table { max-width: 100%; }
                          * { max-width: 100% !important; }
                        </style>
                      </head>
                      <body>
                        ${email.body}
                      </body>
                    </html>
                  `}
                className="w-full min-h-[calc(100vh-350px)] border-0"
                sandbox="allow-same-origin"
                title="Email content"
              />
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            No content available
          </div>
        )}
      </div>
      <Separator className="mt-auto" />
    </div>
  );
}
