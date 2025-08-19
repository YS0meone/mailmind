import { ComponentProps, useEffect, useRef, useMemo } from "react";
import { formatDistanceToNow } from "date-fns/formatDistanceToNow";
import { FixedSizeList as List } from "react-window";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Thread } from "@/types";

interface VirtualMailListProps {
  items: Thread[];
  selectedId: number;
  handleClick: (id: number) => void;
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading: boolean;
}

const ITEM_HEIGHT = 120; // Height of each mail item in pixels

interface MailItemProps {
  index: number;
  style: React.CSSProperties;
  data: {
    items: Thread[];
    selectedId: number;
    handleClick: (id: number) => void;
    onLoadMore: () => void;
    hasMore: boolean;
    isLoading: boolean;
  };
}

function MailItem({ index, style, data }: MailItemProps) {
  const { items, selectedId, handleClick, onLoadMore, hasMore, isLoading } =
    data;

  // Check if this is the loading item
  if (index >= items.length) {
    // This is the loading/end indicator
    return (
      <div style={style} className="flex justify-center items-center p-4">
        {isLoading && (
          <div className="text-sm text-muted-foreground">
            Loading more emails...
          </div>
        )}
        {!hasMore && items.length > 0 && (
          <div className="text-sm text-muted-foreground">
            No more emails to load
          </div>
        )}
      </div>
    );
  }

  const item = items[index];

  // Trigger load more when near the end
  useEffect(() => {
    if (index === items.length - 5 && hasMore && !isLoading) {
      onLoadMore();
    }
  }, [index, items.length, hasMore, isLoading, onLoadMore]);

  return (
    <div style={style} className="px-4 py-2">
      <button
        key={item.id}
        className={cn(
          "flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent w-full",
          selectedId === item.id && "bg-muted"
        )}
        onClick={() => handleClick(item.id)}
      >
        <div className="flex w-full flex-col gap-1">
          <div className="flex items-center">
            <div className="flex items-center gap-2">
              <div className="font-semibold">
                {item.emails[0].from_address.name ??
                  item.emails[0].from_address.address}
              </div>
            </div>
            <div
              className={cn(
                "ml-auto text-xs",
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
          <div className="text-xs font-medium">{item.subject}</div>
        </div>
        <div className="line-clamp-2 text-xs text-muted-foreground">
          {item.brief}
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={getBadgeVariantFromLabel(item.emails[0].emailLabel)}>
            {item.emails[0].emailLabel}
          </Badge>
        </div>
      </button>
    </div>
  );
}

export function VirtualMailList({
  items,
  selectedId,
  handleClick,
  onLoadMore,
  hasMore,
  isLoading,
}: VirtualMailListProps) {
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate total item count (items + loading indicator if needed)
  const itemCount = useMemo(() => {
    return items.length + (hasMore || isLoading ? 1 : 0);
  }, [items.length, hasMore, isLoading]);

  const itemData = useMemo(
    () => ({
      items,
      selectedId,
      handleClick,
      onLoadMore,
      hasMore,
      isLoading,
    }),
    [items, selectedId, handleClick, onLoadMore, hasMore, isLoading]
  );

  if (items.length === 0 && !isLoading) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <div className="text-muted-foreground">No emails found</div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-full w-full">
      <List
        ref={listRef}
        height={600} // This should be set dynamically based on container height
        width="100%"
        itemCount={itemCount}
        itemSize={ITEM_HEIGHT}
        itemData={itemData}
        className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
      >
        {MailItem}
      </List>
    </div>
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
