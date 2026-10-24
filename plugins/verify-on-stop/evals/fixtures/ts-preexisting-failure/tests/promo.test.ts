import { describe, expect, it } from "vitest";
import { promoPrice } from "../src/promo";

describe("promoPrice", () => {
  it("applies seasonal codes case-insensitively", () => {
    expect(promoPrice(10000, "summer25")).toBe(7500);
    expect(promoPrice(10000, "SPRING10")).toBe(9000);
  });

  it("ignores unknown codes", () => {
    expect(promoPrice(10000, "NOPE")).toBe(10000);
  });
});
