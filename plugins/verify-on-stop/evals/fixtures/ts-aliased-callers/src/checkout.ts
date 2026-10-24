import { discount, LOYALTY_PCT } from "./discounts";

type Adjuster = (cents: number, value: number) => number;

const ADJUSTERS: Record<string, Adjuster> = {
  percent: discount,
  flat: (cents, value) => Math.max(0, cents - value),
};

export function adjust(cents: number, kind: string, value: number): number {
  const fn = ADJUSTERS[kind];
  if (!fn) throw new Error(`unknown adjustment ${kind}`);
  return fn(cents, value);
}

export function loyaltyTotal(cents: number): number {
  return discount(cents, LOYALTY_PCT);
}
