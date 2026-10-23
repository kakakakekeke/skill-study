from crm.models import Contact


class Directory:
    def __init__(self, contacts: list[Contact]) -> None:
        self._by_id = {c.id: c for c in contacts}

    def all(self) -> list[Contact]:
        return list(self._by_id.values())

    def get(self, contact_id: int) -> Contact:
        return self._by_id[contact_id]


def find_contact(directory: Directory, contact_id: int) -> Contact:
    """Look up a contact by id. Raises KeyError when the id is unknown."""
    return directory.get(contact_id)
