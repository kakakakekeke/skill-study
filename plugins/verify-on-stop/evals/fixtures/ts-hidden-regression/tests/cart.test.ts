import { describe, expect, it } from "vitest";
import { Cart } from "../src/cart";

describe("Cart", () => {
  it("sums lines with per-line discounts", () => {
    const cart = new Cart();
    cart.add("A", 1000, 2);
    cart.add("B", 500, 1, 10);
    expect(cart.subtotal()).toBe(2500);
    expect(cart.total()).toBe(2450);
  });
});
