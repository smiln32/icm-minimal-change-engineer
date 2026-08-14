"""Invoice storage.

Backed by SQLite; see decisions/approved/0001-storage-sqlite.md.

Boundary rule: customer records are private to this module. Nothing outside
storage reaches into _CUSTOMERS; a public accessor is defined here instead.
"""

_CUSTOMERS = {
    "c-100": {"name": "Ridgeline Foods", "discount_override": 0.25},
    "c-101": {"name": "Bay Supply", "discount_override": None},
}

_INVOICES = {
    "inv-1": {"customer": "c-100", "unit_price": 10.0, "quantity": 12},
    "inv-2": {"customer": "c-101", "unit_price": 4.0, "quantity": 3},
    "inv-3": {"customer": "c-100", "unit_price": 2.5, "quantity": 40},
}


def get_invoice(invoice_id):
    """Return the invoice record, or None if it does not exist."""
    return _INVOICES.get(invoice_id)


def find_invoices(customer_id, limit=2):
    """Invoice ids for a customer, capped at `limit`."""
    found = []
    for invoice_id in sorted(_INVOICES):
        if _INVOICES[invoice_id]["customer"] == customer_id:
            found.append(invoice_id)
    return found[:limit]
