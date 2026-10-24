import { applyDiscount } from "./pricing";

export interface Line {
  sku: string;
  unitPrice: number;
  qty: number;
  discountPct: number;
}

export class Cart {
  readonly lines: Line[] = [];

  add(sku: string, unitPrice: number, qty = 1, discountPct = 0): void {
    this.lines.push({ sku, unitPrice, qty, discountPct });
  }

  subtotal(): number {
    return this.lines.reduce((sum, ln) => sum + ln.unitPrice * ln.qty, 0);
  }

  total(): number {
    return this.lines.reduce((sum, ln) => sum + applyDiscount(ln.unitPrice * ln.qty, ln.discountPct), 0);
  }
}
