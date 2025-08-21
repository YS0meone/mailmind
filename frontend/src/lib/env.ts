export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  const trimmed = configured?.trim();
  if (trimmed && trimmed.length > 0) {
    return trimmed.replace(/\/$/, "");
  }
  if (process.env.NODE_ENV === "development") {
    return "http://localhost:8000";
  }
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}


