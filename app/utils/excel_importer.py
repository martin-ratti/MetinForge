import csv
import os
from typing import Dict, List, Any
from app.utils.logger import logger

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

def parse_account_file(file_path: str) -> Dict[str, Any]:
    """
    Parsea un archivo Excel (.xlsx) o CSV (.csv) con datos de cuentas y personajes.
    
    Formato esperado:
    - Fila con headers (detecta 'Cantidad' o 'Pj'+'Fragmentos')
    - Fila con nombre de tienda/email 
    - Filas de datos: [Cuenta, Slots, NombrePJ]
    
    Returns:
        Dict con 'email' y 'characters' [{slots, name, account_name}]
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        return _parse_csv(file_path)
    elif ext == '.xlsx':
        if not HAS_OPENPYXL:
            raise ImportError("openpyxl es necesario para parsear .xlsx. Instale o use .csv")
        return _parse_xlsx(file_path)
    else:
        raise ValueError(f"Formato no soportado: {ext}")

def _parse_csv(file_path: str) -> Dict[str, Any]:
    data = {"email": "", "characters": []}
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
        if not rows:
            return data
            
        raw_email = rows[0][0].strip()
        if raw_email and "@" not in raw_email:
            data["email"] = f"{raw_email}@gmail.com"
        else:
            data["email"] = raw_email
        
        for row in rows[2:]:
            if len(row) >= 3:
                try:
                    account_name = row[0].strip()
                    slots = int(row[1])
                    name = row[2].strip()
                    if name and account_name:
                        data["characters"].append({
                            "slots": slots, 
                            "name": name,
                            "account_name": account_name
                        })
                except ValueError:
                    continue
                    
    return data

def _parse_xlsx(file_path: str) -> Dict[str, Any]:
    data = {"email": "", "characters": []}
    
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    
    # Cargar todas las filas como strings
    all_rows = []
    for row in ws.iter_rows(values_only=True):
        all_rows.append([str(c).strip() if c is not None else "" for c in row])
    
    # 1. Detectar fila de headers y columnas
    header_row_idx = -1
    slots_col_idx = -1
    name_col_idx = -1
    
    for i, row_strs in enumerate(all_rows):
        if i > 10: break
        row_lower = [s.lower() for s in row_strs]
        
        # Formato A: Headers con 'Cantidad' + 'Alquimero/Pj/Mezclador'
        if "cantidad" in row_lower:
            header_row_idx = i
            for idx, val in enumerate(row_lower):
                if "cantidad" in val: slots_col_idx = idx
                elif any(x in val for x in ["alquimero", "pj", "personaje", "mezclador", "nombre"]): name_col_idx = idx
            break
            
        # Formato B: Headers con 'Pj' + 'Fragmentos'
        elif "fragmentos" in row_lower and "pj" in row_lower:
            header_row_idx = i
            for idx, val in enumerate(row_lower):
                if "pj" in val: slots_col_idx = idx
                elif "fragmentos" in val: name_col_idx = idx
            break
            
    # 2. Detectar Email/Tienda (buscar en filas alrededor del header, ignorando fechas)
    found_email = ""
    start_data_row = 3
    
    if header_row_idx != -1:
        for i in range(min(10, len(all_rows))):
             if i == header_row_idx: continue
             
             row_vals = [x for x in all_rows[i] if x]
             if not row_vals: continue
             
             txt = row_vals[0]
             
             if "/" in txt or "-" in txt or "202" in txt:
                 continue
             if "cantidad" in txt.lower() or "pj" in txt.lower():
                 continue
             
             if len(txt) > 2:
                 found_email = txt
                 break
                 
        start_data_row = header_row_idx + 2
        
    if found_email:
         if "@" not in found_email:
            data["email"] = f"{found_email}@gmail.com"
         else:
            data["email"] = found_email
    else:
         data["email"] = str(ws.cell(row=1, column=1).value or "").strip()
         if data["email"] and "@" not in data["email"] and len(data["email"]) > 2 and "/" not in data["email"] and "-" not in data["email"]:
              data["email"] += "@gmail.com"

    # 3. Parsear datos
    if slots_col_idx == -1: slots_col_idx = 1
    if name_col_idx == -1: name_col_idx = 2
    
    for row_idx in range(start_data_row, ws.max_row + 1):
        try:
             account_val = ws.cell(row=row_idx, column=1).value
             name_val = ws.cell(row=row_idx, column=name_col_idx + 1).value
             
             if not name_val: continue
             
             slots_val = ws.cell(row=row_idx, column=slots_col_idx + 1).value
             
             slots = int(slots_val) if slots_val is not None else 5
             name = str(name_val).strip()
             account_name = str(account_val).strip() if account_val else ""
             
             if name:
                 data["characters"].append({
                        "slots": slots, 
                        "name": name,
                        "account_name": account_name
                 })
        except:
            continue
            
    return data
