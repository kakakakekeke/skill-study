import type { Contact } from "./models";

export class Directory {
  private byId: Map<number, Contact>;

  constructor(contacts: Contact[]) {
    this.byId = new Map(contacts.map((c) => [c.id, c]));
  }

  all(): Contact[] {
    return [...this.byId.values()];
  }

  get(contactId: number): Contact {
    const contact = this.byId.get(contactId);
    if (!contact) throw new Error(`unknown contact id ${contactId}`);
    return contact;
  }
}

/** Look up a contact by id. Throws when the id is unknown. */
export function findContact(directory: Directory, contactId: number): Contact {
  return directory.get(contactId);
}
