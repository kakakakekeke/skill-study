import { describe, expect, it } from "vitest";
import { Directory, reminderSubject, welcomeMessage, type Contact } from "../src";

const ALICE: Contact = { id: 1, name: "Alice Park", email: "alice@example.com", tier: "pro" };
const BOB: Contact = { id: 2, name: "Bob Lee", email: "bob@example.com", tier: "free" };

describe("notify", () => {
  it("builds the welcome message", () => {
    expect(welcomeMessage(new Directory([ALICE, BOB]), 1)).toBe(
      "Welcome, Alice Park! We'll reach you at alice@example.com.",
    );
  });

  it("labels reminders by tier", () => {
    const d = new Directory([ALICE, BOB]);
    expect(reminderSubject(d, 1)).toBe("[Pro] Reminder for Alice");
    expect(reminderSubject(d, 2)).toBe("[Free] Reminder for Bob");
  });
});
