import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Basic slugify tailored to backend expectations (spaces -> '-', '+' -> 'plus', remove non-alphanum/-)
export function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/\+/g, ' plus ') // expand plus for readability
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
  .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

// Reverse slug (best effort) if needed later
export function unslugify(slug: string): string {
  return slug.replace(/-/g, ' ').replace(/\bplus\b/g, '+').replace(/\band\b/g, '&')
}
