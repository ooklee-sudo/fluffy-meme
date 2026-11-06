from src.shipping import shipping_cost


def test_standard_small():
    assert shipping_cost(2.0) == 7.50


def test_express():
    assert shipping_cost(2.0, express=True) == 15.00


def test_zero_weight():
    assert shipping_cost(0.0) == 4.00


def test_legacy_partner_rate():
    # SHIP-142: legacy partner contract rate for a 2 kg parcel
    assert shipping_cost(2) == 8.00
