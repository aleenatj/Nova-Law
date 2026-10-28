import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
}

type CurrencyType = "euro" | "dollar" | "usd" | "eur" | "gbp" | "pound" | "yen" | "jpy" | "inr" | "rupee";

const currencySymbols: Record<CurrencyType, string> = {
  euro: "€",
  eur: "€",
  dollar: "$",
  usd: "$",
  gbp: "£",
  pound: "£",
  yen: "¥",
  jpy: "¥",
  inr: "₹",
  rupee: "₹",
};

export function formatCurrency(
  currency: CurrencyType,
  amount?: number | string
): string {
  const symbol = currencySymbols[currency] || "";
  if (amount === undefined) return symbol;
  return `${symbol}\u2009${amount}`;
}


export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// Helper to capitalize first letter of a string
const capitalize = (str: string): string => 
  str ? str.charAt(0).toUpperCase() + str.slice(1).toLowerCase() : str;

/** Convert string to title case (e.g. "john doe" -> "John Doe") */
export function toTitleCase(str: string): string {
  if (!str || typeof str !== "string") return str;
  return str.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Return the first name from a full name string (e.g. "John Smith" -> "John") */
export function getFirstName(fullName: string | null | undefined): string {
  if (fullName == null || typeof fullName !== "string") return "";
  const trimmed = fullName.trim();
  if (!trimmed) return "";
  return trimmed.split(/\s+/)[0] ?? "";
}

// Function to replace placeholders in text with actual names
export function replacePlaceholders(
  text: string, 
  userName: string = "", 
  partnerName: string = "your partner"
): string {
  if (!text) return text;
  
  return text
    .replace(/{name}/g, toTitleCase(userName))
    .replace(/{partner_name}/g, toTitleCase(partnerName));
}

// Session Storage Keys
const RESOLVE_ID_KEY = "resolveId";

/**
 * Gets the resolve URL, creating a new resolve if one doesn't exist in sessionStorage
 * @returns Promise<string> - The resolve URL to navigate to
 */
export async function getResolveUrl(): Promise<string> {
  // Check if there's an existing resolve ID in session storage
  const existingResolveId = sessionStorage.getItem(RESOLVE_ID_KEY);
  
  if (existingResolveId) {
    return `/resolve/${existingResolveId}`;
  }
  
  // No existing resolve, create a new one
  try {
    // Dynamically import api to avoid circular dependencies
    const { api } = await import("./api");
    const result = await api.get("/v1/resolve");
    const resolveIdFromResult = (result as any)?.data?.resolve_id;
    
    if (resolveIdFromResult) {
      sessionStorage.setItem(RESOLVE_ID_KEY, resolveIdFromResult);
      return `/resolve/${resolveIdFromResult}`;
    }
    
    // Fallback if no resolve ID in response
    throw new Error("Failed to create new resolve");
  } catch (error) {
    console.error("Error creating new resolve:", error);
    // Fallback to /resolve if API call fails
    return "/resolve";
  }
}

export interface ImageUploadOptions {
  file: File;
  entityType: string;
  maxSizeMB?: number;
  allowedTypes?: string[];
  onProgress?: (isUploading: boolean) => void;
}

export interface ImageUploadResult {
  fileKey: string;
  previewUrl: string;
}

/**
 * Generic function to upload an image file to S3 via the backend API
 * 
 * @param options - Upload options including file, entityType, maxSizeMB, allowedTypes, and onProgress callback
 * @returns Promise resolving to ImageUploadResult with fileKey and previewUrl
 * @throws Error if validation or upload fails
 */
export async function uploadImage(
  options: ImageUploadOptions
): Promise<ImageUploadResult> {
  const {
    file,
    entityType,
    maxSizeMB = 5,
    allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "image/gif",
      "image/webp",
    ],
    onProgress,
  } = options;

  // Validate file type
  if (!allowedTypes.includes(file.type)) {
    const errorMsg = "Please select a valid image file (JPEG, PNG, GIF, or WebP)";
    throw new Error(errorMsg);
  }

  // Validate file size
  const maxSize = maxSizeMB * 1024 * 1024; // Convert MB to bytes
  if (file.size > maxSize) {
    const errorMsg = `Image file size must be less than ${maxSizeMB}MB`;
    throw new Error(errorMsg);
  }

  // Notify progress start
  onProgress?.(true);

  try {
    // Create preview URL
    const previewUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target?.result as string);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

    // Get file extension
    const fileExtension = file.name.split(".").pop()?.toLowerCase() || "";

    // Dynamically import api to avoid circular dependencies
    const { api } = await import("./api");

    // Call the upload token API
    const params = new URLSearchParams({
      extension: fileExtension,
      entity_type: entityType,
    });

    const response = (await api.get(
      `/v1/upload/get-file-upload-token?${params}`
    )) as any;

    // If we have a valid upload_url, do the PUT to S3
    if (
      response &&
      response.data &&
      response.data.upload_url &&
      response.data.file_key
    ) {
      // Do the PUT request to S3
      const uploadUrl = response.data.upload_url;
      const putResult = await fetch(uploadUrl, {
        method: "PUT",
        headers: {
          "Content-Type": file.type,
        },
        body: file,
      });

      if (!putResult.ok) {
        throw new Error("Failed to upload image to storage.");
      }

      const fileKey = response.data.file_key;
      
      // Notify progress end
      onProgress?.(false);
      
      return { fileKey, previewUrl };
    } else {
      throw new Error("Invalid upload token response.");
    }
  } catch (error: any) {
    console.error("Failed to upload image:", error);
    // Notify progress end on error
    onProgress?.(false);
    throw new Error(error.message || "Failed to upload image. Please try again.");
  }
} 