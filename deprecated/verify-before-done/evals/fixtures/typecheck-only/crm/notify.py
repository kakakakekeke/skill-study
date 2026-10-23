from crm.directory import Directory, find_contact


def welcome_message(directory: Directory, contact_id: int) -> str:
    contact = find_contact(directory, contact_id)
    return f"Welcome, {contact.name}! We'll reach you at {contact.email}."


def reminder_subject(directory: Directory, contact_id: int) -> str:
    contact = find_contact(directory, contact_id)
    label = "Pro" if contact.tier == "pro" else "Free"
    return f"[{label}] Reminder for {contact.name.split()[0]}"
