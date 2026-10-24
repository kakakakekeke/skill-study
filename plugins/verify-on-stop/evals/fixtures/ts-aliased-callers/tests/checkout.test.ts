import { describe, expect, it } from "vitest";
import { adjust, loyaltyTotal } from "../src/checkout";

describe("checkout", () => {
  it("applies the loyalty discount", () => {
    expect(loyaltyTotal(10000)).toBe(9500);
  });

  it("supports percent and flat adjustments", () => {
    expect(adjust(10000, "percent", 20)).toBe(8000);
    expect(adjust(10000, "flat", 1500)).toBe(8500);
  });
});
