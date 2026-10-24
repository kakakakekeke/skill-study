import { applyDiscount } from "./pricing";

const SEASONAL: Record<string, number> = { SPRING10: 10, SUMMER25: 25 };

export function promoPrice(price: number, code: string): number {
  const pct = SEASONAL[code.toUpperCase()] ?? 0;
  return applyDiscount(price, pct);
}
