const normalizeUrl = (url: string) => url.replace(/\/$/, "");

export const API_BASE_URL = normalizeUrl(
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
);

const defaultWs = API_BASE_URL.replace(/^http/i, (match) =>
  match.toLowerCase() === "https" ? "wss" : "ws"
);

export const WS_BASE_URL = normalizeUrl(
  process.env.NEXT_PUBLIC_WS_URL ?? defaultWs
);

export const PRIMARY_WALLET_ADDRESS =
  process.env.NEXT_PUBLIC_PRIMARY_WALLET_ADDRESS ??
  "0x1234000000000000000000000000000000001234";

export const PRIMARY_AGENT_TYPE =
  process.env.NEXT_PUBLIC_PRIMARY_AGENT_TYPE ?? "planner";

export const SECONDARY_NETWORK =
  process.env.NEXT_PUBLIC_SECONDARY_NETWORK ?? "polygon_amoy";
