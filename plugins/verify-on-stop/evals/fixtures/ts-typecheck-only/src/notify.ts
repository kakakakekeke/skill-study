import { Directory, findContact } from "./directory";

export function welcomeMessage(directory: Directory, contactId: number): string {
  const contact = findContact(directory, contactId);
  return `Welcome, ${contact.name}! We'll reach you at ${contact.email}.`;
}

export function reminderSubject(directory: Directory, contactId: number): string {
  const contact = findContact(directory, contactId);
  const label = contact.tier === "pro" ? "Pro" : "Free";
  return `[${label}] Reminder for ${contact.name.split(" ")[0]}`;
}
