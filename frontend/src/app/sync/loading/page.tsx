"use client";
import { useEffect, useState } from "react";
import { Loader2, Mail, AlertCircle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getApiBaseUrl } from "@/lib/env";

export default function SyncLoadingPage() {
  const [state, setState] = useState<{
    state: string;
    processed?: string | number;
    error?: string;
  }>({ state: "running" });

  const backend = getApiBaseUrl();

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
        if (!cancelled) setTimeout(poll, 20000);
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [backend]);

  const isError = state.state === "error";

  return (
    <main className="relative min-h-screen bg-card">
      <div className="relative z-10 flex min-h-screen items-center justify-center p-6">
        <Card className="w-full max-w-lg border-none shadow-none">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <Mail className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">
              {isError ? "Sync failed" : "Setting up your inbox"}
            </CardTitle>
            <CardDescription>
              {isError
                ? "We couldn't fetch your emails. Please go back and try again."
                : "We are fetching your emails. This might take a few minutes depending on your mailbox size."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!isError ? (
              <div className="mt-2 flex flex-col items-center gap-3" aria-busy>
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <p className="text-xs text-muted-foreground">Preparing…</p>
              </div>
            ) : (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Sync failed</AlertTitle>
                <AlertDescription className="break-words">
                  {state.error}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
