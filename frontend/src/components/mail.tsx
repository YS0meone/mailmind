"use client";

import * as React from "react";
import { usePaginatedThreads } from "@/hooks/use-paginated-threads";
import { useMailSearch } from "@/hooks/use-mail-search";
import { Loader2, File, Inbox, Search, Send, RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { MailDisplay } from "@/components/mail-display";
import { MailList } from "@/components/mail-list";
import { Nav } from "@/components/nav";
import { Chat } from "@/components/chat";
import { MailHeader } from "@/components/mail-header";
import { DbEmail, Thread } from "@/types";
import { useCurrentUser } from "@/hooks/use-current-user";
import { getApiBaseUrl } from "@/lib/env";

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
  const [selecteId, setSelectedId] = React.useState<string>("");
  const { user } = useCurrentUser();

  // Use the new paginated hook
  const {
    threads,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    loadMore,
    refresh,
    addThread,
  } = usePaginatedThreads();

  // Use search functionality
  const {
    searchQuery,
    setSearchQuery,
    filteredThreads,
    isSearching,
    clearSearch,
  } = useMailSearch(threads);

  // Use filtered threads for display
  const displayThreads = filteredThreads;

  function handleClick(id: string): void {
    setSelectedId(id);
  }

  const handleEmailSelect = async (threadId: string) => {
    console.log("onEmailSelect called with threadId:", threadId);

    // First try to find in currently loaded threads
    const thread = displayThreads.find(
      (t: Thread) =>
        t.id.toString() === threadId ||
        t.emails.some(
          (email: DbEmail) =>
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
          `${getApiBaseUrl()}/mail/thread/${threadId}`,
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

          // Add the thread to our current threads using the hook function
          addThread(fetchedThread);
          setSelectedId(fetchedThread.id);
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

  if (isLoading) {
    return (
      <div className="relative flex min-h-screen items-center justify-center p-6">
        <Card className="w-full max-w-lg text-center border-none shadow-none">
          <CardHeader className="items-center text-center">
            <div className="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
              <Inbox className="h-7 w-7 text-primary" />
            </div>
            <CardTitle className="text-xl">Loading your inbox</CardTitle>
            <CardDescription>
              Fetching your latest emails. This should only take a moment.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mt-2 flex flex-col items-center gap-3" aria-busy>
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <p className="text-xs text-muted-foreground">
                Preparing threads…
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-2">Error loading emails</p>
          <button
            onClick={refresh}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Try Again
          </button>
        </div>
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
          maxSize={30}
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
              <Button
                variant="ghost"
                size="sm"
                className="ml-2"
                onClick={refresh}
                disabled={isLoading || isLoadingMore}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4",
                    (isLoading || isLoadingMore) && "animate-spin"
                  )}
                />
              </Button>
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
              <form onSubmit={(e) => e.preventDefault()}>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search emails..."
                    className="pl-8"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  {searchQuery && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-1 top-1 h-7 w-7 p-0"
                      onClick={clearSearch}
                    >
                      ×
                    </Button>
                  )}
                </div>
              </form>
            </div>
            <TabsContent
              value="all"
              className="m-0 flex-1 overflow-hidden flex flex-col"
            >
              <MailList
                items={displayThreads}
                selectedId={selecteId}
                handleClick={handleClick}
                onLoadMore={searchQuery ? () => {} : loadMore} // Disable pagination when searching
                hasMore={searchQuery ? false : hasMore}
                isLoading={searchQuery ? isSearching : isLoadingMore}
              />
            </TabsContent>
            <TabsContent
              value="done"
              className="m-0 flex-1 overflow-hidden flex flex-col"
            >
              <MailList
                items={displayThreads.filter((item: Thread) => item.done)}
                selectedId={selecteId}
                handleClick={handleClick}
                onLoadMore={searchQuery ? () => {} : loadMore} // Disable pagination when searching
                hasMore={searchQuery ? false : hasMore}
                isLoading={searchQuery ? isSearching : isLoadingMore}
              />
            </TabsContent>
          </Tabs>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={defaultLayout[2]} minSize={30}>
          <MailDisplay
            thread={
              displayThreads.find((item: Thread) => item.id === selecteId) ||
              null
            }
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </TooltipProvider>
  );
}
