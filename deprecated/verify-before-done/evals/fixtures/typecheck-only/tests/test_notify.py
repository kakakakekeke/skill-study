from crm import Contact, Directory, reminder_subject, welcome_message

ALICE = Contact(1, "Alice Park", "alice@example.com", "pro")
BOB = Contact(2, "Bob Lee", "bob@example.com")


def test_welcome_message():
    d = Directory([ALICE, BOB])
    assert welcome_message(d, 1) == "Welcome, Alice Park! We'll reach you at alice@example.com."


def test_reminder_subject_tier():
    d = Directory([ALICE, BOB])
    assert reminder_subject(d, 1) == "[Pro] Reminder for Alice"
    assert reminder_subject(d, 2) == "[Free] Reminder for Bob"
