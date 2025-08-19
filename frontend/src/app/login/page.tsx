import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/login-form";
import { Mail } from "lucide-react";

export default async function LoginPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (token) {
    // verify token server-side with a lightweight call to backend /auth/me
    try {
      const api =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${api}/auth/me`, {
        headers: { Cookie: `access_token=${token}` },
        cache: "no-store",
      });
      if (res.ok) {
        redirect("/inbox");
      }
    } catch {}
  }

  return (
    <main className="min-h-screen grid md:grid-cols-2">
      <div className="relative hidden md:flex items-center justify-center bg-muted/50 p-10">
        <div className="absolute inset-0 bg-gradient-to-br from-background/0 via-background/20 to-background/60" />
        <div className="relative z-10 max-w-md text-center">
          <div className="mx-auto mb-6 h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Mail className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome to MailMind
          </h1>
          <p className="mt-2 text-muted-foreground">
            Your AI-powered inbox for faster triage, smarter replies, and
            focused work.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center md:hidden">
            <h1 className="text-2xl font-semibold">Welcome to MailMind</h1>
            <p className="text-sm text-muted-foreground">Sign in to continue</p>
          </div>
          <LoginForm />
        </div>
      </div>
    </main>
  );
}
