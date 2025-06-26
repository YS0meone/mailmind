import { useState, useCallback, useEffect, useMemo } from 'react';
import { Thread } from '@/types';

interface UseMailSearchResult {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredThreads: Thread[];
  isSearching: boolean;
  clearSearch: () => void;
}

export function useMailSearch(threads: Thread[]): UseMailSearchResult {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Filter threads based on search query
  const filteredThreads = useMemo(() => {
    if (!searchQuery.trim()) {
      return threads;
    }

    const query = searchQuery.toLowerCase().trim();
    
    return threads.filter(thread => {
      // Search in subject
      if (thread.subject.toLowerCase().includes(query)) {
        return true;
      }
      
      // Search in brief
      if (thread.brief.toLowerCase().includes(query)) {
        return true;
      }
      
      // Search in sender's name and email
      for (const email of thread.emails) {
        if (email.from_address.name?.toLowerCase().includes(query) ||
            email.from_address.address.toLowerCase().includes(query)) {
          return true;
        }
      }
      
      // Search in email labels
      for (const email of thread.emails) {
        if (email.emailLabel.toLowerCase().includes(query)) {
          return true;
        }
      }
      
      return false;
    });
  }, [threads, searchQuery]);

  // Debounced search effect
  useEffect(() => {
    if (searchQuery.trim()) {
      setIsSearching(true);
      const timeout = setTimeout(() => {
        setIsSearching(false);
      }, 300);
      
      return () => clearTimeout(timeout);
    } else {
      setIsSearching(false);
    }
  }, [searchQuery]);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setIsSearching(false);
  }, []);

  return {
    searchQuery,
    setSearchQuery,
    filteredThreads,
    isSearching,
    clearSearch
  };
}
