import React from "react";

export interface PaginationConfig {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
}

export interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

// Simple pagination hook
export function usePagination(totalItems: number, itemsPerPage: number) {
  const [currentPage, setCurrentPage] = React.useState(1);

  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const hasNextPage = currentPage < totalPages;
  const hasPreviousPage = currentPage > 1;

  // Reset to page 1 when totalItems changes (new data loaded)
  React.useEffect(() => {
    setCurrentPage(1);
  }, [totalItems]);

  const goToPage = React.useCallback(
    (page: number) => {
      if (page >= 1 && page <= totalPages && totalPages > 0) {
        setCurrentPage(page);
      }
    },
    [totalPages]
  );

  const goToNextPage = React.useCallback(() => {
    if (hasNextPage) {
      setCurrentPage((prev) => prev + 1);
    }
  }, [hasNextPage]);

  const goToPreviousPage = React.useCallback(() => {
    if (hasPreviousPage) {
      setCurrentPage((prev) => prev - 1);
    }
  }, [hasPreviousPage]);

  return {
    currentPage,
    totalPages,
    totalItems,
    itemsPerPage,
    hasNextPage,
    hasPreviousPage,
    goToPage,
    goToNextPage,
    goToPreviousPage,
  };
}

// Basic pagination component
export function Pagination({ config }: { config: PaginationConfig }) {
  const { currentPage, totalPages, totalItems, itemsPerPage, onPageChange } =
    config;
  const hasNextPage = currentPage < totalPages;
  const hasPreviousPage = currentPage > 1;

  // if (totalPages <= 1) return null;

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    // Use 768 for mobile so tablets and phones get reduced button count (tailwind 'md')
    const isSmallScreen =
      typeof window !== "undefined" && window.innerWidth < 768;
    // Mobile: 1,2,...,n. Desktop: 1,2,3,4,5,...,n
    const maxVisiblePages = isSmallScreen ? 2 : 5;
    const startEndCount = isSmallScreen ? 1 : 4; // mobile: 2 at start/end; desktop: 5 at start/end

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const showEllipsis = totalPages > maxVisiblePages;

      if (currentPage <= startEndCount + 1) {
        // Near start: 1,2,3,...,n (mobile) or 1,2,3,4,5,...,n (desktop)
        for (let i = 1; i <= Math.min(startEndCount + 1, totalPages); i++) {
          pages.push(i);
        }
        if (showEllipsis && totalPages > startEndCount + 2) {
          pages.push("...");
        }
        if (totalPages > startEndCount + 1) {
          pages.push(totalPages);
        }
      } else if (currentPage >= totalPages - startEndCount) {
        // Near end: 1,...,n-2,n-1,n (mobile) or 1,...,last 5 (desktop)
        if (totalPages > startEndCount + 1) {
          pages.push(1);
        }
        if (showEllipsis && totalPages > startEndCount + 2) {
          pages.push("...");
        }
        for (let i = Math.max(1, totalPages - startEndCount); i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Middle: 1,...,current,...,n (mobile) or 1,...,current±1,...,n (desktop)
        const half = isSmallScreen ? 0 : 1;
        pages.push(1);
        pages.push("...");
        for (let i = currentPage - half; i <= currentPage + half; i++) {
          pages.push(i);
        }
        pages.push("...");
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <div className="flex flex-row items-start justify-start w-full gap-2 sm:gap-3">
      {/* Pagination controls */}
      <div className="flex flex-row items-center justify-center gap-0 sm:gap-1">
        {/* Previous button */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPreviousPage}
          aria-label="Previous page"
          className="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md sm:rounded-lg border border-novaNeutral-300 text-novaNeutral-400 sm:text-novaNeutral-500 bg-white hover:bg-novaNeutral-50 hover:text-novaNeutral-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 text-base sm:text-sm"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          <span className="hidden sm:inline ml-2">Previous</span>
        </button>

        {/* Page numbers */}
        <div className="flex items-center gap-0.5 sm:gap-1 max-w-full px-0.5 sm:px-1 overflow-x-auto scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-transparent">
          {getPageNumbers().map((page, index) => (
            <button
              key={index}
              onClick={() =>
                typeof page === "number" ? onPageChange(page) : undefined
              }
              disabled={page === "..."}
              aria-current={page === currentPage ? "page" : undefined}
              className={`
                min-w-[26px] sm:min-w-[38px] px-1 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm font-medium rounded-md sm:rounded-lg border transition-colors duration-150 shrink-0
                ${
                  page === currentPage
                    ? "bg-novaPrimary-600 text-white border-novaPrimary-600 hover:bg-novaPrimary-700 focus:outline-none focus-visible:outline focus-visible:outline-1 focus-visible:outline-white focus-visible:-outline-offset-2"
                    : page === "..."
                    ? "bg-transparent text-novaNeutral-300 border-novaNeutral-100 cursor-default select-none"
                    : "bg-white text-novaNeutral-700 border-novaNeutral-300 hover:bg-novaNeutral-50 hover:text-novaNeutral-900"
                }
                ${page === "..." ? "pointer-events-none" : ""}
                ${page === currentPage ? "z-10 shadow-novaPrimary-100 shadow" : ""}
              `}
              tabIndex={page === "..." ? -1 : 0}
            >
              {page}
            </button>
          ))}
        </div>

        {/* Next button */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNextPage}
          aria-label="Next page"
          className="flex items-center justify-center px-2 sm:px-3 py-1.5 sm:py-2 rounded-md sm:rounded-lg border border-novaNeutral-300 text-novaNeutral-400 sm:text-novaNeutral-500 bg-white hover:bg-novaNeutral-50 hover:text-novaNeutral-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 text-base sm:text-sm"
        >
          <span className="hidden sm:inline mr-2">Next</span>
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
      <div className="text-xs sm:text-sm text-novaNeutral-500 italic text-center items-center my-auto">
        {/* Compact (count/count) for small screens, full summary for sm and up */}
        <span className="sm:hidden">
          <strong>
            {Math.min(currentPage * itemsPerPage, totalItems)}
          </strong>
          {"/"}
          <strong>{totalItems}</strong>
        </span>
        <span className="hidden sm:inline">
          Showing <strong>{totalItems === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1}</strong>
          {" to "}
          <strong>{Math.min(currentPage * itemsPerPage, totalItems)}</strong>
          {" of "}
          <strong>{totalItems}</strong>
          {" result"}
          {totalItems === 1 ? "" : "s"}
        </span>
      </div>
    </div>
  );
}

// Utility functions
export function getPageItems<T>(
  items: T[],
  currentPage: number,
  itemsPerPage: number
): T[] {
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  return items.slice(startIndex, endIndex);
}

export function getTotalPages(
  totalItems: number,
  itemsPerPage: number
): number {
  return Math.ceil(totalItems / itemsPerPage);
}
