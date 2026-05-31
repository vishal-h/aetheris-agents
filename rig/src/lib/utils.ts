import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format bytes to human-readable file size
 * @param bytes - Number of bytes
 * @returns Formatted string (e.g., "1.2 MB", "340 KB")
 */
export function formatBytes(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = bytes / Math.pow(k, i);

  // Show 1 decimal place for values >= 10, 2 decimals for smaller values
  const decimals = value >= 10 ? 1 : 2;

  return `${value.toFixed(decimals)} ${units[i]}`;
}

/**
 * Format Unix timestamp to YYYY-MM-DD
 * @param timestamp - Unix timestamp in seconds
 * @returns Formatted date string
 */
export function formatDate(timestamp: number | null): string {
  if (timestamp === null || timestamp === undefined) return '—';

  const date = new Date(timestamp * 1000); // Convert seconds to milliseconds
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}
