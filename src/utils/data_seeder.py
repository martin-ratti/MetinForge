import os
import sys
import openpyxl
from datetime import date, timedelta

# Aseguramos que Python encuentre los módulos
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.config import Config
from src.models.models import StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType

def parse_and_seed_excel(file_path):
    engine = create_engine(Config.get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"📂 Procesando Excel: {file_path}...")
    
    try:
        # Cargar el libro de trabajo (data_only=True obtiene los valores, no las fórmulas)
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active # Toma la primera hoja activa
        
        current_store = None
        base_date = date(2024, 1, 1) # Fecha base ficticia para el ejemplo

        # Iterar filas (min_row=2 para saltar encabezados principales)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # row es una tupla: (ColA, ColB, ColC, ...)
            # Indices: 0=Cuenta/Tienda, 1=Cantidad, 2=Personaje, 3=Dia1...
            
            col0 = str(row[0]).strip() if row[0] else None
            col2_char = str(row[2]).strip() if len(row) > 2 and row[2] else None

            # Si la fila está vacía completamente, saltar
            if not col0 and not col2_char:
                continue

            # --- LOGICA DE DETECCION ---

            # Caso 1: CABECERA DE TIENDA (Ej: "FRAGMETIN5")
            # Condición: Hay texto en Col0, pero NO hay personaje en Col2, y no es "Total Cors" ni fechas
            if col0 and not col2_char:
                if "Total" in col0 or "Fecha" in col0 or "Cantidad" in col0:
                    continue
                
                store_name = col0
                store = session.query(StoreAccount).filter_by(email=store_name).first()
                if not store:
                    store = StoreAccount(email=store_name)
                    session.add(store)
                    session.flush()
                    print(f"  🛒 Tienda: {store_name}")
                current_store = store
                continue

            # Caso 2: PERSONAJE (Tiene nombre de cuenta en Col0 y PJ en Col2)
            if col0 and col2_char and current_store:
                game_acc_name = col0
                char_name = col2_char
                
                # 1. Game Account
                g_acc = session.query(GameAccount).filter_by(username=game_acc_name).first()
                if not g_acc:
                    g_acc = GameAccount(username=game_acc_name, store_account=current_store)
                    session.add(g_acc)
                    session.flush()

                # 2. Character
                character = session.query(Character).filter_by(name=char_name).first()
                if not character:
                    character = Character(name=char_name, game_account=g_acc, char_type=CharacterType.ALCHEMIST)
                    session.add(character)
                    session.flush()
                    print(f"    👤 PJ: {char_name}")

                # 3. Importar Actividad (Columnas 3 en adelante son los dias)
                # row[3] es el primer dia
                for day_idx in range(31): 
                    col_idx = day_idx + 3 
                    if col_idx < len(row):
                        val = row[col_idx]
                        status = 0
                        
                        # Normalizar valores de Excel (pueden venir como int, str o None)
                        if val == 1 or val == '1': status = 1
                        elif val == -1 or val == '-1': status = -1
                        elif val == 0 or val == '0': status = 0
                        else: continue # Celda vacía o valor raro

                        target_date = base_date + timedelta(days=day_idx)
                        
                        # Upsert (Insertar o Ignorar si existe)
                        existing = session.query(DailyCorActivity).filter_by(
                            character_id=character.id, 
                            date=target_date
                        ).first()
                        
                        if not existing:
                            log = DailyCorActivity(
                                date=target_date,
                                status_code=status,
                                character=character
                            )
                            session.add(log)
        
        session.commit()
        print("✅ Importación de EXCEL finalizada con éxito.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error crítico leyendo Excel: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # BUSCAMOS AUTOMATICAMENTE CUALQUIER .xlsx EN LA CARPETA
    files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~$')]
    
    if files:
        target_file = files[0] # Tomamos el primero que encuentre
        parse_and_seed_excel(target_file)
    else:
        print("⚠️ No encontré ningún archivo .xlsx en la carpeta raíz.")
        print("👉 Por favor, coloca tu archivo 'Cors Diarios (2).xlsx' aquí.")
