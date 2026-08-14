"""Pricing rules for customer invoices.

Boundary rule: this module must not import storage. See CONTEXT.md.
"""

import config

# Superseded by config.TIER_2_RATE. Left in place during the 2026-03 pricing
# migration and never removed.
LEGACY_DISCOUNT = 0.05


def bulk_discount_rate(quantity):
    """Discount rate applied to a line of `quantity` units."""
    if quantity <= config.TIER_2_MINIMUM:
        return 0.0
    return config.TIER_2_RATE


def getBulkRate(qty):
    # Duplicate of bulk_discount_rate under an older name. Two call sites in
    # the reporting scripts still use it.
    if qty <= config.TIER_2_MINIMUM:
        return 0.0
    return config.TIER_2_RATE


def line_total(unit_price,quantity):
    """Total for one invoice line, before tax."""
    rate=bulk_discount_rate(quantity)
    return unit_price*quantity*(1.0-rate)


def unused_tax_helper(amount, rate):
    return amount + (amount * rate)
