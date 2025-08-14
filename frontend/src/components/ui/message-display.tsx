import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { format } from "date-fns";
import { DbEmail } from "@/types";
import { useEffect, useRef } from "react";

export default function MessageDisplay({ email }: { email: DbEmail }) {
  console.log(email);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  const adjustIframeHeight = () => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (!doc) return;
      // Reset and measure
      iframe.style.height = "0px";
      const body = doc.body;
      const html = doc.documentElement;
      const height = Math.max(
        body?.scrollHeight || 0,
        body?.offsetHeight || 0,
        html?.clientHeight || 0,
        html?.scrollHeight || 0,
        html?.offsetHeight || 0
      );
      iframe.style.height = `${Math.max(480, height)}px`;
    } catch {
      // ignore cross-origin issues (shouldn't happen with srcDoc)
    }
  };

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    const onLoad = () => {
      adjustIframeHeight();
      // Observe dynamic content changes inside the iframe
      try {
        const doc = iframe.contentDocument || iframe.contentWindow?.document;
        if (!doc) return;
        const observer = new MutationObserver(() => adjustIframeHeight());
        observer.observe(doc.documentElement, {
          subtree: true,
          childList: true,
          characterData: true,
        });
        // Cleanup
        return () => observer.disconnect();
      } catch {
        return;
      }
    };
    iframe.addEventListener("load", onLoad, { once: true });
    return () => iframe.removeEventListener("load", onLoad);
  }, [email?.id]);
  return (
    <div className="flex flex-col">
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
      <div className="overflow-hidden">
        {email.body ? (
          <div className="p-4">
            <div className="border rounded-md">
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
                ref={iframeRef}
                className="w-full border-0"
                sandbox="allow-same-origin"
                title="Email content"
                onLoad={adjustIframeHeight}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center p-6 text-muted-foreground">
            No content available
          </div>
        )}
      </div>
      <Separator />
    </div>
  );
}
