export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "none";
}
