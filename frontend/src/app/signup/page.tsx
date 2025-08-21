"use client";
import React from "react";
import Link from "next/link";
import { getApiBaseUrl } from "@/lib/env";
import { Mail } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  const handleGoogleSignup = () => {
    const baseUrl = "https://api.aurinko.io/v1/auth/authorize";
    const appClientId = process.env.NEXT_PUBLIC_AURINKO_CLIENT_ID || "";
    const backend = getApiBaseUrl();
    console.log(baseUrl, appClientId, backend);
    const params = new URLSearchParams({
      clientId: appClientId,
      serviceType: "Google",
      scopes: "Mail.Read Mail.Send",
      responseType: "code",
      returnUrl: `${backend}/auth/callback`,
      state: JSON.stringify({ source: "signup", timestamp: Date.now() }),
    });
    window.location.href = `${baseUrl}?${params.toString()}`;
  };

  return (
    <main className="min-h-screen grid md:grid-cols-2">
      <div className="relative hidden md:flex items-center justify-center bg-muted/50 p-10">
        <div className="absolute inset-0 bg-gradient-to-br from-background/0 via-background/20 to-background/60" />
        <div className="relative z-10 max-w-md text-center">
          <div className="mx-auto mb-6 h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Mail className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Join MailMind</h1>
          <p className="mt-2 text-muted-foreground">
            Connect your mailbox and let AI organize your inbox.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center md:hidden">
            <h1 className="text-2xl font-semibold">Create your account</h1>
            <p className="text-sm text-muted-foreground">
              Sign up to get started
            </p>
          </div>
          <Card className="w-full">
            <CardHeader className="text-center">
              <CardTitle className="text-xl">Create your account</CardTitle>
              <CardDescription>
                Sign up with Google to connect your mailbox.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleGoogleSignup}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    className="mr-2 h-4 w-4"
                  >
                    <path
                      d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                      fill="currentColor"
                    />
                  </svg>
                  Sign up with Google
                </Button>
                <div className="text-center text-sm">
                  Already have an account?{" "}
                  <Link href="/login" className="underline underline-offset-4">
                    Sign in
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
