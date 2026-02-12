import openpyxl

file_path = "Cors Diarios.xlsx"
try:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    print(f"--- Browsing {file_path} ---")
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i > 5: break
        clean_row = [str(c).strip() if c is not None else "None" for c in row]
        print(f"Row {i}: {clean_row}")
except Exception as e:
    print(f"Error: {e}")
