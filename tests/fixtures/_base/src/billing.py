"""Pricing rules for customer invoices.

Boundary rule: this module must not import storage. See CONTEXT.md.
"""

import config


def bulk_discount_rate(quantity):
    """Discount rate applied to a line of `quantity` units."""
    if quantity < config.TIER_2_MINIMUM:
        return 0.0
    return config.TIER_2_RATE


def line_total(unit_price, quantity):
    """Total for one invoice line, before tax."""
    rate = bulk_discount_rate(quantity)
    return unit_price * quantity * (1.0 - rate)
