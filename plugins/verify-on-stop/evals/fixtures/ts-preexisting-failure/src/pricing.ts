/** Return price (integer cents) reduced by pct percent (0-100), rounded to the nearest cent. */
export function applyDiscount(price: number, pct: number): number {
  return Math.round((price * (100 - pct)) / 100);
}

const SYMBOLS: Record<string, string> = { USD: "$", EUR: "EUR", GBP: "£" };

export function formatPrice(cents: number, currency = "USD"): string {
  const symbol = SYMBOLS[currency] ?? `${currency} `;
  return `${symbol}${(cents / 100).toFixed(2)}`;
}
