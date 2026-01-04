'use client';

import { useState, useMemo } from 'react';

interface UsePaginationProps<T> {
  items: T[];
  itemsPerPage: number;
}

interface UsePaginationReturn<T> {
  displayedItems: T[];
  hasMore: boolean;
  loadMore: () => void;
  loading: boolean;
  reset: () => void;
  currentPage: number;
  totalPages: number;
}

export function usePagination<T>({ 
  items, 
  itemsPerPage 
}: UsePaginationProps<T>): UsePaginationReturn<T> {
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [itemsLength, setItemsLength] = useState(items.length);

  // Reset pagination when items array changes
  if (items.length !== itemsLength) {
    setItemsLength(items.length);
    setCurrentPage(1);
    setLoading(false);
  }

  const totalPages = Math.ceil(items.length / itemsPerPage);
  const hasMore = currentPage < totalPages;

  const displayedItems = useMemo(() => {
    return items.slice(0, currentPage * itemsPerPage);
  }, [items, currentPage, itemsPerPage]);

  const loadMore = () => {
    if (hasMore && !loading) {
      setLoading(true);
      // Simulate loading delay for better UX
      setTimeout(() => {
        setCurrentPage(prev => prev + 1);
        setLoading(false);
      }, 300);
    }
  };

  const reset = () => {
    setCurrentPage(1);
    setLoading(false);
  };

  return {
    displayedItems,
    hasMore,
    loadMore,
    loading,
    reset,
    currentPage,
    totalPages
  };
}