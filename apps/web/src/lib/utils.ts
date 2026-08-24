// utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS classes safely.
 * Resolves conflicts (e.g., `p-2 p-4` becomes `p-4`) and handles conditional arrays.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}