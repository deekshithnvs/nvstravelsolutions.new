from decimal import Decimal

def test_tax_calc(tax_amount, cgst, sgst, igst):
    # This is the logic used in the router
    # f"₹{(float(inv.tax_amount) if inv.tax_amount else (float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0))):,.2f}"
    
    # Simulating the expression
    # Note: in the router it's float(inv.tax_amount) if inv.tax_amount else ...
    # If inv.tax_amount is Decimal('0.00'), then bool(inv.tax_amount) is False.
    
    tax_val = float(tax_amount) if tax_amount else (float(cgst or 0) + float(sgst or 0) + float(igst or 0))
    return tax_val

print(f"Decimal(0.00): {test_tax_calc(Decimal('0.00'), 451.51, 451.51, 0.0)}")
print(f"0.0: {test_tax_calc(0.0, 451.51, 451.51, 0.0)}")
print(f"None: {test_tax_calc(None, 451.51, 451.51, 0.0)}")
print(f"100.0: {test_tax_calc(100.0, 451.51, 451.51, 0.0)}")
