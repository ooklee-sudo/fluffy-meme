def shipping_cost(weight_kg, express=False):
    """Return the shipping cost in EUR for a parcel.

    Pricing rules (see docs/PRICING.md):
      - base fee: 4.00
      - plus 1.75 per kg
      - express delivery doubles the total
    The result is rounded to 2 decimals.
    """
    raise NotImplementedError("SHIP-142")
