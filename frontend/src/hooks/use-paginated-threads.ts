import { useState, useCallback, useEffect, useRef } from 'react';
import useSWR from 'swr';
import { Thread } from '@/types';

const fetcher = (url: string) =>
  fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  }).then((res) => {
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return res.json();
  });

interface UsePaginatedThreadsResult {
  threads: Thread[];
  isLoading: boolean;
  isLoadingMore: boolean;
  error: any;
  hasMore: boolean;
  loadMore: () => void;
  refresh: () => void;
  addThread: (thread: Thread) => void;
  totalCount: number;
  removeThread: (threadId: number) => void;
  updateThread: (threadId: number, updates: Partial<Thread>) => void;
}

const ITEMS_PER_PAGE = 20;

export function usePaginatedThreads(): UsePaginatedThreadsResult {
  const [currentPage, setCurrentPage] = useState(1);
  const [allThreads, setAllThreads] = useState<Thread[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const loadingRef = useRef(false);

  // Fetch data for the current page
  const params = new URLSearchParams({
    page: currentPage.toString(),
    limit: ITEMS_PER_PAGE.toString(),
  });

  const {
    data: pageData,
    error,
    isLoading,
    mutate
  } = useSWR<Thread[]>(
    `http://localhost:8000/mail/threads?${params.toString()}`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 30000, // Cache for 30 seconds
      errorRetryCount: 3,
      errorRetryInterval: 1000,
      keepPreviousData: true, // Keep previous data while loading new data
      refreshInterval: 0, // Disable auto refresh
    }
  );

  // Update allThreads when new page data arrives
  useEffect(() => {
    console.log('Page data effect triggered:', {
      pageData: pageData?.length,
      currentPage,
      error,
      isLoading
    });
    
    if (pageData) {
      if (currentPage === 1) {
        console.log('Setting initial threads:', pageData.length);
        // First page - replace all threads
        setAllThreads(pageData);
      } else {
        console.log('Appending new threads to existing:', pageData.length);
        // Subsequent pages - append to existing threads
        setAllThreads(prev => {
          // Avoid duplicates by filtering out threads that already exist
          const existingIds = new Set(prev.map(thread => thread.id));
          const newThreads = pageData.filter(thread => !existingIds.has(thread.id));
          console.log('New unique threads to add:', newThreads.length);
          return [...prev, ...newThreads];
        });
      }

      // Check if we have more data to load
      const hasMoreData = pageData.length === ITEMS_PER_PAGE;
      console.log('Setting hasMore to:', hasMoreData, 'based on pageData length:', pageData.length);
      setHasMore(hasMoreData);
      setIsLoadingMore(false);
      loadingRef.current = false;
    }
  }, [pageData, currentPage]);

  // Load more function with debouncing
  const loadMore = useCallback(() => {
    console.log('loadMore called with state:', {
      isLoading,
      isLoadingMore,
      hasMore,
      loadingRefCurrent: loadingRef.current,
      currentPage,
      threadsLength: allThreads.length
    });
    
    if (!isLoading && !isLoadingMore && hasMore && !loadingRef.current) {
      console.log('Incrementing page from', currentPage, 'to', currentPage + 1);
      loadingRef.current = true;
      setIsLoadingMore(true);
      setCurrentPage(prev => prev + 1);
    } else {
      console.log('loadMore blocked by conditions');
    }
  }, [isLoading, isLoadingMore, hasMore, currentPage, allThreads.length]);

  // Refresh function to reload from the beginning
  const refresh = useCallback(() => {
    setCurrentPage(1);
    setAllThreads([]);
    setHasMore(true);
    setIsLoadingMore(false);
    loadingRef.current = false;
    mutate();
  }, [mutate]);

  // Add a single thread (useful for real-time updates)
  const addThread = useCallback((thread: Thread) => {
    setAllThreads(prev => {
      // Check if thread already exists
      const existingIndex = prev.findIndex(t => t.id === thread.id);
      if (existingIndex >= 0) {
        // Update existing thread
        const updated = [...prev];
        updated[existingIndex] = thread;
        return updated;
      } else {
        // Add new thread at the beginning
        return [thread, ...prev];
      }
    });
  }, []);

  // Remove a thread
  const removeThread = useCallback((threadId: number) => {
    setAllThreads(prev => prev.filter(thread => thread.id !== threadId));
  }, []);

  // Update a specific thread
  const updateThread = useCallback((threadId: number, updates: Partial<Thread>) => {
    setAllThreads(prev => 
      prev.map(thread => 
        thread.id === threadId 
          ? { ...thread, ...updates }
          : thread
      )
    );
  }, []);

  return {
    threads: allThreads,
    isLoading: isLoading && currentPage === 1, // Only show loading for initial load
    isLoadingMore,
    error,
    hasMore,
    loadMore,
    refresh,
    addThread,
    removeThread,
    updateThread,
    totalCount: allThreads.length
  };
}
