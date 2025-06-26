"use client";

import * as React from "react";
import useSWR from "swr";
import {
  AlertCircle,
  Archive,
  ArchiveX,
  File,
  Inbox,
  MessagesSquare,
  Search,
  Send,
  ShoppingCart,
  Trash2,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MailDisplay } from "@/components/mail-display";
import { MailList } from "@/components/mail-list";
import { Nav } from "@/components/nav";
import { Chat } from "@/components/chat";
import { MailHeader } from "@/components/mail-header";
import { Mail, DbEmail, Thread } from "@/types";
import { convertDbEmailsToMails } from "@/lib/utils";
import { useCurrentUser } from "@/hooks/use-current-user";

const fetcher = (url: string) =>
  fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  }).then((res) => res.json());

interface MailProps {
  defaultLayout: number[] | undefined;
  defaultCollapsed?: boolean;
  navCollapsedSize: number;
}

export function MailPage({
  defaultLayout = [20, 40, 40],
  defaultCollapsed = false,
  navCollapsedSize,
}: MailProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed);
  const [selecteId, setSelectedId] = React.useState(0);
  const { user } = useCurrentUser();

  function handleClick(id: number): void {
    setSelectedId(id);
  }

  const handleEmailSelect = async (threadId: string) => {
    console.log("onEmailSelect called with threadId:", threadId);

    // First try to find in currently loaded threads
    const thread = threads.find(
      (t) =>
        t.id.toString() === threadId ||
        t.emails.some(
          (email) =>
            email.id.toString() === threadId ||
            email.threadId.toString() === threadId
        )
    );

    if (thread) {
      console.log("Found thread in loaded threads:", thread.id);
      setSelectedId(thread.id);
    } else {
      console.log("Thread not in loaded threads, fetching...");
      try {
        // Fetch the specific thread by threadId
        const response = await fetch(
          `http://localhost:8000/mail/thread/${threadId}`,
          {
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (response.ok) {
          const fetchedThread = await response.json();
          console.log("Fetched thread:", fetchedThread);

          // Add the thread to our current threads if it's not already there
          const existingThread = threads.find((t) => t.id === fetchedThread.id);
          if (!existingThread && fetchedThreads) {
            // Update the SWR cache with the new thread
            const updatedThreads = [fetchedThread, ...fetchedThreads];
            // You might need to use SWR's mutate function here
            setSelectedId(fetchedThread.id);
          } else if (existingThread) {
            setSelectedId(existingThread.id);
          }
        } else {
          console.log("Failed to fetch thread:", response.status);
          alert(
            "Could not load the selected email. It might not be in your current mailbox."
          );
        }
      } catch (error) {
        console.error("Error fetching thread:", error);
        alert("Error loading the selected email.");
      }
    }
  };

  const params = new URLSearchParams({
    page: "1",
    limit: "20",
  });
  let {
    data: fetchedThreads,
    error,
    isLoading,
  } = useSWR<Thread[]>(
    `http://localhost:8000/mail/threads?${params.toString()}`,
    fetcher
  );

  const threads = fetchedThreads ?? [];

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">Loading...</div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        Error loading threads
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={0}>
      <ResizablePanelGroup
        direction="horizontal"
        onLayout={(sizes: number[]) => {
          document.cookie = `react-resizable-panels:layout:mail=${JSON.stringify(
            sizes
          )}`;
        }}
        className="h-full max-h-screen items-stretch"
      >
        <ResizablePanel
          defaultSize={defaultLayout[0]}
          collapsedSize={navCollapsedSize}
          collapsible={true}
          minSize={15}
          maxSize={20}
          onCollapse={() => {
            setIsCollapsed(true);
            document.cookie = `react-resizable-panels:collapsed=${JSON.stringify(
              true
            )}`;
          }}
          onResize={() => {
            setIsCollapsed(false);
            document.cookie = `react-resizable-panels:collapsed=${JSON.stringify(
              false
            )}`;
          }}
          className={cn(
            isCollapsed &&
              "min-w-[50px] transition-all duration-300 ease-in-out"
          )}
        >
          <div className="flex flex-col h-full">
            <MailHeader
              isCollapsed={isCollapsed}
              userEmail={user?.email}
              userName={user?.name}
            />
            <Separator />
            <Nav
              isCollapsed={isCollapsed}
              links={[
                {
                  title: "Inbox",
                  label: "128",
                  icon: Inbox,
                  variant: "default",
                },
                {
                  title: "Drafts",
                  label: "9",
                  icon: File,
                  variant: "ghost",
                },
                {
                  title: "Sent",
                  label: "",
                  icon: Send,
                  variant: "ghost",
                },
              ]}
            />
            <Separator />
            {!isCollapsed && (
              <div className="flex-1 min-h-0">
                <Chat onEmailSelect={handleEmailSelect} />
              </div>
            )}
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={defaultLayout[1]} minSize={30}>
          <Tabs defaultValue="all" className="flex flex-col h-full">
            <div className="flex items-center px-4 py-2 flex-shrink-0">
              <h1 className="text-xl font-bold">Inbox</h1>
              <TabsList className="ml-auto">
                <TabsTrigger
                  value="all"
                  className="text-zinc-600 dark:text-zinc-200"
                >
                  All mail
                </TabsTrigger>
                <TabsTrigger
                  value="done"
                  className="text-zinc-600 dark:text-zinc-200"
                >
                  Done
                </TabsTrigger>
              </TabsList>
            </div>
            <Separator />
            <div className="bg-background/95 p-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex-shrink-0">
              <form>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search" className="pl-8" />
                </div>
              </form>
            </div>
            <TabsContent
              value="all"
              className="m-0 flex-1 overflow-hidden flex flex-col"
            >
              <MailList
                items={threads}
                selectedId={selecteId}
                handleClick={handleClick}
              />
            </TabsContent>
            <TabsContent
              value="done"
              className="m-0 flex-1 overflow-hidden flex flex-col"
            >
              <MailList
                items={threads.filter((item) => item.done)}
                selectedId={selecteId}
                handleClick={handleClick}
              />
            </TabsContent>
          </Tabs>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={defaultLayout[2]} minSize={30}>
          <MailDisplay
            thread={threads.find((item) => item.id === selecteId) || null}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </TooltipProvider>
  );
}
