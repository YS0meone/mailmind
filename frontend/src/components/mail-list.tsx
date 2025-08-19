import { ComponentProps, useEffect, useRef, useCallback } from "react";
import { formatDistanceToNow } from "date-fns/formatDistanceToNow";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Thread } from "@/types";

interface MailListProps {
  items: Thread[];
  selectedId: string;
  handleClick: (id: string) => void;
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading: boolean;
}

export function MailList({
  items,
  selectedId,
  handleClick,
  onLoadMore,
  hasMore,
  isLoading,
}: MailListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef<HTMLDivElement>(null);
  const isLoadingRef = useRef(false);

  // Intersection Observer for infinite scrolling
  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      console.log("Intersection Observer triggered:", {
        isIntersecting: target.isIntersecting,
        hasMore,
        isLoading,
        isLoadingRefCurrent: isLoadingRef.current,
        itemsLength: items.length,
      });

      if (
        target.isIntersecting &&
        hasMore &&
        !isLoading &&
        !isLoadingRef.current
      ) {
        console.log("Calling onLoadMore...");
        isLoadingRef.current = true;
        onLoadMore();
        // Reset loading ref after a delay to prevent rapid calls
        setTimeout(() => {
          isLoadingRef.current = false;
        }, 1000);
      }
    },
    [onLoadMore, hasMore, isLoading, items.length]
  );

  useEffect(() => {
    const element = loadingRef.current;
    if (!element) {
      console.log("Loading ref element not found");
      return;
    }

    const option = {
      root: null, // Use viewport as root instead of scrollRef
      rootMargin: "100px", // Trigger earlier
      threshold: 0.1,
    };

    console.log("Setting up intersection observer with options:", option);
    const observer = new IntersectionObserver(handleObserver, option);
    observer.observe(element);

    return () => {
      console.log("Cleaning up intersection observer");
      observer.unobserve(element);
    };
  }, [handleObserver]);

  // Reset loading ref when isLoading changes
  useEffect(() => {
    if (!isLoading) {
      isLoadingRef.current = false;
    }
  }, [isLoading]);

  // Fallback scroll detection
  useEffect(() => {
    const scrollElement = scrollRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    ) as HTMLElement;
    if (!scrollElement) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollElement;
      const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;

      // console.log("Scroll event:", {
      //   scrollTop,
      //   scrollHeight,
      //   clientHeight,
      //   scrollPercentage,
      //   hasMore,
      //   isLoading,
      //   isLoadingRefCurrent: isLoadingRef.current,
      // });

      // Trigger load more when user has scrolled 90% of the way down
      if (
        scrollPercentage > 0.9 &&
        hasMore &&
        !isLoading &&
        !isLoadingRef.current
      ) {
        console.log("Triggering loadMore via scroll detection");
        isLoadingRef.current = true;
        onLoadMore();
        setTimeout(() => {
          isLoadingRef.current = false;
        }, 1000);
      }
    };

    scrollElement.addEventListener("scroll", handleScroll);
    return () => scrollElement.removeEventListener("scroll", handleScroll);
  }, [hasMore, isLoading, onLoadMore]);

  if (items.length === 0 && !isLoading) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <div className="text-muted-foreground">No emails found</div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full" ref={scrollRef}>
      <div className="flex flex-col gap-2 p-4 pt-0">
        {items.map((item) => (
          <button
            key={item.id}
            className={cn(
              "flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent",
              selectedId === item.id && "bg-muted"
            )}
            onClick={() => handleClick(item.id)}
          >
            <div className="flex w-full flex-col gap-1">
              <div className="flex items-center">
                <div className="flex items-center gap-2">
                  <div className="font-semibold truncate max-w-48">
                    {item.emails[0].from_address.name ??
                      item.emails[0].from_address.address}
                  </div>
                  {/* {!item.read && (
                    <span className="flex h-2 w-2 rounded-full bg-blue-600" />
                  )} */}
                </div>
                <div
                  className={cn(
                    "ml-auto text-xs shrink-0",
                    selectedId === item.id
                      ? "text-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {formatDistanceToNow(new Date(item.lastMessageDate), {
                    addSuffix: true,
                  })}
                </div>
              </div>
              <div className="text-xs font-medium truncate">{item.subject}</div>
            </div>
            <div className="line-clamp-2 text-xs text-muted-foreground">
              {item.brief}
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant={getBadgeVariantFromLabel(item.emails[0].emailLabel)}
              >
                {item.emails[0].emailLabel}
              </Badge>
            </div>
          </button>
        ))}

        {/* Loading indicator and intersection target */}
        <div
          ref={loadingRef}
          className="flex justify-center p-4 min-h-[60px] bg-red-100"
          style={{ border: "2px solid red" }} // Temporary debug styling
        >
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
              Loading more emails...
            </div>
          )}
          {!hasMore && items.length > 0 && (
            <div className="text-sm text-muted-foreground">
              No more emails to load
            </div>
          )}
          {hasMore && !isLoading && items.length > 0 && (
            <div className="text-xs text-muted-foreground">
              Scroll to load more... (hasMore: {hasMore.toString()}, items:{" "}
              {items.length})
            </div>
          )}
        </div>
      </div>
    </ScrollArea>
  );
}

function getBadgeVariantFromLabel(
  label: string
): ComponentProps<typeof Badge>["variant"] {
  if (["work"].includes(label.toLowerCase())) {
    return "default";
  }

  if (["personal"].includes(label.toLowerCase())) {
    return "outline";
  }

  return "secondary";
}
