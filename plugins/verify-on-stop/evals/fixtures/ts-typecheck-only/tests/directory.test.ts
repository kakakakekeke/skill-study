import { describe, expect, it } from "vitest";
import { Directory, findContact, type Contact } from "../src";

const ALICE: Contact = { id: 1, name: "Alice Park", email: "alice@example.com", tier: "pro" };
const BOB: Contact = { id: 2, name: "Bob Lee", email: "bob@example.com", tier: "free" };

describe("findContact", () => {
  it("returns a known contact", () => {
    expect(findContact(new Directory([ALICE, BOB]), 2)).toEqual(BOB);
  });

  it("throws for an unknown id", () => {
    expect(() => findContact(new Directory([ALICE]), 99)).toThrow();
  });
});
