import { describe, expect, it } from "vitest";
import { applyDiscount, formatPrice } from "../src/pricing";

describe("applyDiscount", () => {
  it("applies a percent discount", () => {
    expect(applyDiscount(2000, 15)).toBe(1700);
  });

  it("rounds to the nearest cent", () => {
    expect(applyDiscount(999, 33)).toBe(669);
  });

  it("is a no-op at 0%", () => {
    expect(applyDiscount(1234, 0)).toBe(1234);
  });
});

describe("formatPrice", () => {
  it("formats USD and EUR", () => {
    expect(formatPrice(1999)).toBe("$19.99");
    expect(formatPrice(500, "EUR")).toBe("€5.00");
  });
});
