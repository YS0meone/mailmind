"use client";
import { useEffect, useState } from "react";

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
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-2xl font-semibold">
          {isError ? "Sync failed" : "Setting up your inbox"}
        </h1>
        <p className="text-muted-foreground">
          {isError
            ? "We couldn't fetch your emails. Please go back and try again."
            : "We are fetching your emails. This might take a few minutes depending on your mailbox size."}
        </p>
        {!isError && (
          <p className="text-sm text-muted-foreground">
            Processed: {state.processed ?? 0}
          </p>
        )}
        {isError && (
          <p className="text-sm text-red-600 break-words">{state.error}</p>
        )}
      </div>
    </main>
  );
}
