"use client";
import React, { useState } from "react";
import Link from "next/link";
import { Mail } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SignupCompletePage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [syncDaysWithin, setSyncDaysWithin] = useState<number>(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const backend =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (syncDaysWithin < 1 || syncDaysWithin > 365) {
      setError("Sync days must be between 1 and 365");
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch(`${backend}/auth/signup/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ password, syncDaysWithin }),
      });
      if (!resp.ok) {
        const detail = await resp.text();
        throw new Error(detail || "Failed to complete signup");
      }
      // Redirect to syncing page; the worker will run the initial sync
      window.location.href = "/sync/loading";
    } catch (err: any) {
      setError(err?.message || "Failed to complete signup");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen grid md:grid-cols-2">
      <div className="relative hidden md:flex items-center justify-center bg-muted/50 p-10">
        <div className="absolute inset-0 bg-gradient-to-br from-background/0 via-background/20 to-background/60" />
        <div className="relative z-10 max-w-md text-center">
          <div className="mx-auto mb-6 h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Mail className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Finish setting up
          </h1>
          <p className="mt-2 text-muted-foreground">
            Create your password and choose how many days of email to sync.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center md:hidden">
            <h1 className="text-2xl font-semibold">Complete your setup</h1>
            <p className="text-sm text-muted-foreground">
              Secure your account and set preferences
            </p>
          </div>
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Complete your setup</CardTitle>
              <CardDescription>
                Set your password and choose how many days of email to sync.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="grid gap-6">
                <div className="grid gap-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                  <p className="text-xs text-muted-foreground">
                    Minimum 8 characters
                  </p>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="syncDays">Days to sync</Label>
                  <Input
                    id="syncDays"
                    type="number"
                    min={1}
                    max={365}
                    value={syncDaysWithin}
                    onChange={(e) => setSyncDaysWithin(Number(e.target.value))}
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    We recommend 30–90 days for faster initial sync.
                  </p>
                </div>
                {error && <div className="text-sm text-red-600">{error}</div>}
                <div className="flex items-center gap-3">
                  <Button type="submit" disabled={loading} className="flex-1">
                    {loading ? "Saving..." : "Save and sync"}
                  </Button>
                  <Link
                    href="/inbox"
                    className="text-sm underline underline-offset-4 text-muted-foreground"
                  >
                    Skip for now
                  </Link>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
