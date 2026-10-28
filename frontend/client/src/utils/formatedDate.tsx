export function formatTimestamp(timestamp: string | null, dateOnly: boolean = false): string {
    if (!timestamp) return "";

    // Normalize to ISO 8601 with Z if only missing Z (likely UTC):
    let normalized = timestamp;
    if (
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,6}$/.test(timestamp)
    ) {
        // If missing 'Z', add it (treat as UTC -- API convention)
        normalized += "Z";
    }

    const date = new Date(normalized);

    // Fallback for invalid dates
    if (isNaN(date.getTime())) return "";

    // Always display time in UTC, as that's what API probably provides
    const day = String(date.getUTCDate()).padStart(2, "0");
    const month = String(date.getUTCMonth() + 1).padStart(2, "0");
    const year2 = String(date.getUTCFullYear()).slice(-2);

    if (dateOnly) {
        return `${day}/${month}/${year2}`;
    }

    let hours = date.getUTCHours();
    const minutes = String(date.getUTCMinutes()).padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    if (hours === 0) hours = 12; // Midnight or Noon should be 12
    const hourString = String(hours).padStart(2, "0");

    return `${day}/${month}/${year2} at ${hourString}:${minutes} ${ampm}`;
}