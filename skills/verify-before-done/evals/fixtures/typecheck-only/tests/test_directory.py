import pytest

from crm import Contact, Directory, find_contact

ALICE = Contact(1, "Alice Park", "alice@example.com", "pro")
BOB = Contact(2, "Bob Lee", "bob@example.com")


def test_find_contact_known():
    d = Directory([ALICE, BOB])
    assert find_contact(d, 2) == BOB


def test_find_contact_unknown_raises():
    d = Directory([ALICE])
    with pytest.raises(KeyError):
        find_contact(d, 99)
