from app.utils.excel_importer import _parse_list_from_rows

# Mock Data equivalent to Cors Diarios.xlsx
rows = [
    ['Cors Diarios', None, None],
    [None, None, None],
    ['Cuenta', 'Pj', 'Fragmentos'], # Header at idx 2
    ['Fragmetin1', 5, 'ChamanLuzPVM'], # Data at idx 3. Pj=5 (Int), Frag=Name
    ['Fragmetin8', '5', 'Melano']       # Data at idx 4. Pj='5' (Str), Frag=Name
]

print("Parsing Mock Data...")
result = _parse_list_from_rows(rows)
print(f"Result: {result}")

# Expectations:
# Email: Fragmetin1 -> Chars: name='ChamanLuzPVM', slots=5
# Email: Fragmetin8 -> Chars: name='Melano', slots=5

for acc in result:
    print(f"Account: {acc['email']}")
    for char in acc['characters']:
        print(f"  - Char: {char['name']} (Slots: {char.get('slots')})")
