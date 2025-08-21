import { cookies } from "next/headers";
import Image from "next/image";
import { redirect } from "next/navigation";
import { MailPage } from "@/components/mail";
import { getApiBaseUrl } from "@/lib/env";

export default async function InboxPage() {
  // Basic auth guard: require access_token cookie
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) {
    redirect("/login");
  }
  // Double-check token by calling backend; if invalid/expired, redirect to login
  const api = getApiBaseUrl();
  try {
    const res = await fetch(`${api}/auth/me`, {
      headers: { Cookie: `access_token=${token}` },
      cache: "no-store",
    });
    if (!res.ok) {
      redirect("/login");
    }
  } catch {
    redirect("/login");
  }
  const cookiesStore = await cookies();
  const layout = cookiesStore.get("react-resizable-panels:layout:mail");
  const collapsed = cookiesStore.get("react-resizable-panels:collapsed");

  const defaultLayout = layout ? JSON.parse(layout.value) : undefined;
  const defaultCollapsed = collapsed ? JSON.parse(collapsed.value) : undefined;

  return (
    <>
      <div className="md:hidden">
        <Image
          src="/examples/mail-dark.png"
          width={1280}
          height={727}
          alt="Mail"
          className="hidden dark:block"
        />
        <Image
          src="/examples/mail-light.png"
          width={1280}
          height={727}
          alt="Mail"
          className="block dark:hidden"
        />
      </div>
      <div className="hidden flex-col md:flex">
        <MailPage
          defaultLayout={defaultLayout}
          defaultCollapsed={defaultCollapsed}
          navCollapsedSize={4}
        />
      </div>
    </>
  );
}
