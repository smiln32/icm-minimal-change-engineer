"""Invoice assembly."""

import billing


def invoice_total(lines):
    """Total for a list of (unit_price, quantity) lines, before tax.

    Returns a raw float: the cents rounding required before an invoice is
    issued is not applied here yet.
    """
    total = 0.0
    for unit_price, quantity in lines:
        total += billing.line_total(unit_price, quantity)
    return total
