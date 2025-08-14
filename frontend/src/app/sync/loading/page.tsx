"use client";
import { useEffect, useState } from "react";
import { Loader2, Mail } from "lucide-react";

export default function SyncLoadingPage() {
  const [state, setState] = useState<{
    state: string;
    processed?: string | number;
    error?: string;
  }>({ state: "running" });

  const backend =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const resp = await fetch(`${backend}/sync/status`, {
          credentials: "include",
        });
        const data = await resp.json();
        if (!cancelled) {
          setState(data);
          if (data.state === "done") {
            window.location.href = "/inbox";
          }
        }
      } catch {
        // ignore transient errors, will retry
      } finally {
        if (!cancelled) setTimeout(poll, 2000);
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [backend]);

  const isError = state.state === "error";

  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-background via-muted/40 to-background">
      <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
      <div className="absolute -right-24 -bottom-24 h-72 w-72 rounded-full bg-secondary/10 blur-3xl" />

      <div className="relative z-10 flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-lg rounded-xl border bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/60 p-8 shadow-sm">
          <div className="flex flex-col items-center text-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <Mail className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-2xl font-semibold">
              {isError ? "Sync failed" : "Setting up your inbox"}
            </h1>
            <p className="text-sm text-muted-foreground max-w-prose">
              {isError
                ? "We couldn't fetch your emails. Please go back and try again."
                : "We are fetching your emails. This might take a few minutes depending on your mailbox size."}
            </p>

            {!isError ? (
              <div className="mt-2 flex flex-col items-center gap-3" aria-busy>
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <div className="h-2 w-56 overflow-hidden rounded-full bg-muted">
                  <div className="h-full w-1/3 animate-[progress_1.2s_ease-in-out_infinite] rounded-full bg-primary" />
                </div>
                <p className="text-xs text-muted-foreground">
                  Processed: {state.processed ?? 0}
                </p>
              </div>
            ) : (
              <div className="mt-2">
                <p className="text-sm text-red-600 break-words">
                  {state.error}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* keyframes for indeterminate progress */}
      <style jsx>{`
        @keyframes progress {
          0% {
            transform: translateX(-100%);
          }
          50% {
            transform: translateX(20%);
          }
          100% {
            transform: translateX(120%);
          }
        }
      `}</style>
    </main>
  );
}
