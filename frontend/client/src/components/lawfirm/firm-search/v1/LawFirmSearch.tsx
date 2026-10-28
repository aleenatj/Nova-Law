// components/LawFirmSearch.tsx
import React, { useState, useEffect, useRef, useCallback } from "react";
import { LawFirm } from "@/lib/types";
import { api } from "@/lib/api";

interface LawFirmSearchProps {
  value: string;
  onChange: (firm: LawFirm) => void;
  error?: string;
  placeholder?: string;
}

const LawFirmSearch: React.FC<LawFirmSearchProps> = ({
  value,
  onChange,
  error,
  placeholder = "Search law firm by name...",
}) => {
  const [lawFirms, setLawFirms] = useState<LawFirm[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Sync searchTerm from value prop when value changes externally
  useEffect(() => {
    // If value is cleared externally, also clear searchTerm
    if (!value && searchTerm) {
      setSearchTerm("");
    } else if (value && value !== searchTerm) {
      setSearchTerm(value);
    }
  }, [value]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Fetch law firms
  const fetchLawFirms = useCallback(
    async (pageNum: number, search: string, append: boolean = false) => {
      setLoading(true);
      try {
        const limit = 10;
        const params = new URLSearchParams({
          page: pageNum.toString(),
          limit: limit.toString(),
          status: "Active",
          ...(search && { name: search }),
        });

        const response = (await api.get(`/v1/law-firm?${params}`)) as any;

        if (response.success && response.data) {
          const firms = response.data.law_firms || [];
          const totalCount = response.data.total_count || 0;

          if (append) {
            setLawFirms((prev) => [...prev, ...firms]);
          } else {
            setLawFirms(firms);
          }

          setHasMore(pageNum * limit < totalCount);
        } else {
          console.error("Law firm API response not successful:", response);
        }
      } catch (error) {
        console.error("Failed to fetch law firms:", error);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Load law firms when dropdown opens or search changes
  useEffect(() => {
    if (dropdownOpen) {
      setPage(1);
      fetchLawFirms(1, debouncedSearchTerm);
    }
  }, [debouncedSearchTerm, dropdownOpen, fetchLawFirms]);

  // Handle scroll for infinite loading
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current || loading || !hasMore) return;

    const { scrollTop, scrollHeight, clientHeight } =
      scrollContainerRef.current;
    if (scrollTop + clientHeight >= scrollHeight - 10) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchLawFirms(nextPage, debouncedSearchTerm, true);
    }
  }, [loading, hasMore, page, debouncedSearchTerm, fetchLawFirms]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFirmSelect = (firm: LawFirm) => {
    onChange(firm);
    setSearchTerm(firm.name);
    setDropdownOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);
    
    // If input is cleared (empty), also clear the selection in parent form
    if (!newValue.trim() && value) {
      onChange({} as LawFirm);
    }
    
    if (!dropdownOpen) {
      setDropdownOpen(true);
    }
  };

  const handleInputFocus = () => {
    setDropdownOpen(true);
  };

  const handleClear = () => {
    setSearchTerm("");
    setDropdownOpen(false);
    setLawFirms([]);
    // Call onChange with empty object to clear selection
    onChange({} as LawFirm);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <input
        type="text"
        value={searchTerm}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        className={`w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 ${
          error ? "border-novaCaution-500" : "border-novaNeutral-300"
        }`}
        placeholder={placeholder}
        autoComplete="off"
      />
      {searchTerm && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
          <button
            type="button"
            onClick={handleClear}
            className="text-novaNeutral-400 hover:text-novaNeutral-600 transition-colors"
            title="Clear selection"
          >
            <i className="fas fa-times text-xs"></i>
          </button>
          {value && (
            <i className="fas fa-check text-novaSuccess-500 text-xs"></i>
          )}
        </div>
      )}

      {/* Dropdown */}
      {dropdownOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-novaNeutral-300 rounded-md shadow-lg max-h-60 overflow-hidden">
          <div
            ref={scrollContainerRef}
            onScroll={handleScroll}
            className="max-h-60 overflow-y-auto"
          >
            {lawFirms.length === 0 && !loading ? (
              <div className="px-3 py-2 text-sm text-novaNeutral-500 text-center">
                {debouncedSearchTerm
                  ? "No Organisations found"
                  : "Start typing to search..."}
              </div>
            ) : (
              <>
                {lawFirms.map((firm) => (
                  <div
                    key={firm.id}
                    onClick={() => handleFirmSelect(firm)}
                    className="px-3 py-2 text-sm cursor-pointer transition-colors hover:bg-novaPrimary-50 text-novaNeutral-900"
                  >
                    <div className="font-medium">{firm.name}</div>
                    <div className="text-xs text-novaNeutral-500 mt-0.5">
                      {[firm.city, firm.state].filter(Boolean).join(", ")}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="px-3 py-2 text-sm text-novaNeutral-500 text-center">
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    Loading...
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LawFirmSearch;
