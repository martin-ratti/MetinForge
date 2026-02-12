from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import Config
from app.domain.models import Server, StoreAccount, GameAccount, Character, CharacterType, FishingActivity
from sqlalchemy import extract

from app.application.services.base_service import BaseService
from app.utils.logger import logger

class FishingService(BaseService):
    # __init__ and get_session inherited from BaseController

    def get_fishing_data(self, server_id, year):
        session = self.get_session()
        try:
            # 1. Get all Store Accounts for this server
            # Similar logic to AlchemyController, but filtering for FISHERMAN characters?
            # Or just all characters? The user image shows "Pescador" column.
            # Let's assume we want to show characters that are flagged as FISHERMAN or just show all but highlight fishermen?
            # For now, let's fetch all GameAccounts -> Characters.
            
            # Optimization: We might want to filter only accounts that have fishing chars?
            # But the user might want to add fishing to any char.
            
            stores = session.query(StoreAccount).join(GameAccount).filter(GameAccount.server_id == server_id).distinct().all()
            
            result = []
            
            for store in stores:
                store_data = {
                    'store': store,
                    'accounts': []
                }
                
                # Get GameAccounts for this store & server
                game_accounts = session.query(GameAccount).filter(
                    GameAccount.store_account_id == store.id,
                    GameAccount.server_id == server_id
                ).all()
                
                valid_accounts = []
                for ga in game_accounts:
                    # Match Alchemy Logic: Use first character only
                    if not ga.characters: continue
                    
                    # Sort like Alchemy? usually ID order.
                    # AlchemyController uses: sorted(account.characters, key=lambda x: x.id) in update but straight list in dashboard?
                    # AlchemyView.AlchemyRow uses game_account.characters[0]
                    # Let's ensure we use the same one.
                    first_char = ga.characters[0]
                    
                    # Get activity for this MAIN character
                    activities = session.query(FishingActivity).filter(
                        FishingActivity.character_id == first_char.id,
                        FishingActivity.year == year
                    ).all()
                    
                    # Map: "month_week" -> status
                    act_map = {}
                    for act in activities:
                        key = f"{act.month}_{act.week}"
                        act_map[key] = act.status_code
                    
                    # Attach map to GameAccount (or Char) - matching Alchemy pattern
                    ga.fishing_activity_map = act_map
                    valid_accounts.append(ga)
                
                if valid_accounts:
                    store_data['accounts'] = valid_accounts
                    result.append(store_data)
            
            return result
        
        finally:
            session.close()

    def get_last_filled_week(self, char_id, year):
        """
        Returns (month, week) of the LAST filled slot (status != 0).
        Used for undoing/resetting.
        """
        session = self.get_session()
        try:
            # Order by Month DESC, Week DESC to find the last one
            last_act = session.query(FishingActivity).filter(
                FishingActivity.character_id == char_id,
                FishingActivity.year == year,
                FishingActivity.status_code != 0
            ).order_by(FishingActivity.month.desc(), FishingActivity.week.desc()).first()
            
            if last_act:
                return last_act.month, last_act.week
            return None, None
        except Exception as e:
            logger.error(f"Error getting last filled fishing week: {e}")
            return None, None
        finally:
            session.close()

    def import_fishing_data_from_excel(self, file_path, server_id):
        """
        Imports accounts from Excel/CSV and ensures they exist in DB.
        """
        from app.utils.excel_importer import parse_account_file
        try:
            data = parse_account_file(file_path)
            return self.bulk_import_accounts(server_id, data)
        except Exception as e:
            logger.error(f"Import Error: {e}")
            raise e

    def bulk_import_accounts(self, server_id, import_data):
        """
        Creates accounts and characters from imported data.
        Supports import_data as Dict (single) or List[Dict] (multiple).
        """
        from app.domain.models import StoreAccount, GameAccount, Character, CharacterType
        
        if isinstance(import_data, list):
            total_count = 0
            for item in import_data:
                total_count += self.bulk_import_accounts(server_id, item)
            return total_count

        email = import_data.get("email")
        characters = import_data.get("characters", [])
        
        if not email or not characters:
            return 0
            
        session = self.get_session()
        count = 0
        try:
            # 1. Ensure StoreAccount exists
            store = session.query(StoreAccount).filter_by(email=email).first()
            if not store:
                store = StoreAccount(email=email)
                session.add(store)
                session.flush()
                
            for char_data in characters:
                pj_name = char_data['name']
                
                # Check for explicit account name from import (Table/User format)
                # If not present, fallback to generating from PJ name
                account_name = char_data.get('account_name')
                if not account_name:
                    username = pj_name # No suffix as requested
                else:
                    username = account_name # No suffix as requested
                
                # Check for duplicates by exact username
                existing_acc = session.query(GameAccount).filter_by(username=username).first()
                if not existing_acc:
                    new_acc = GameAccount(
                        username=username,
                        store_account_id=store.id,
                        server_id=server_id
                    )
                    session.add(new_acc)
                    session.flush()
                    
                    new_char = Character(
                        name=pj_name,
                        game_account_id=new_acc.id,
                        char_type=CharacterType.FISHERMAN,
                        slots=slots
                    )
                    session.add(new_char)
                    count += 1
                else:
                    # Account exists. Check if char exists? 
                    # Logic: If account exists, we might need to add char to it if not present?
                    # Check if char with this name exists in this account?
                    existing_char = session.query(Character).filter_by(name=pj_name, game_account_id=existing_acc.id).first()
                    if not existing_char:
                        new_char = Character(
                            name=pj_name,
                            game_account_id=existing_acc.id,
                            char_type=CharacterType.FISHERMAN,
                            slots=slots
                        )
                        session.add(new_char)
                        count += 1
            
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk Import Error: {e}")
            return 0
        finally:
            session.close()

    def update_fishing_status(self, char_id, year, month, week, new_status):
        session = self.get_session()
        try:
            activity = session.query(FishingActivity).filter(
                FishingActivity.character_id == char_id,
                FishingActivity.year == year,
                FishingActivity.month == month,
                FishingActivity.week == week
            ).first()
            
            if activity:
                activity.status_code = new_status
            else:
                activity = FishingActivity(
                    character_id=char_id,
                    year=year,
                    month=month,
                    week=week,
                    status_code=new_status
                )
                session.add(activity)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating fishing status: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_next_pending_week(self, char_id, year):
        """
        Returns the first (month, week) tuple that is pending (0) or missing.
        Sequence: Month 1 Week 1 -> Month 1 Week 2 ... Month 12 Week 4
        """
        session = self.get_session()
        try:
            activities = session.query(FishingActivity).filter_by(
                character_id=char_id, 
                year=year
            ).all()
            
            # Map "m_w" -> status
            status_map = {}
            for act in activities:
                status_map[f"{act.month}_{act.week}"] = act.status_code
            
            # Iterate sequentially
            for m in range(1, 13):
                for w in range(1, 5):
                    key = f"{m}_{w}"
                    if status_map.get(key, 0) == 0:
                        return m, w
            
            # If all done, return last valid slot or something else?
            return 12, 4
            
        except Exception as e:
            logger.error(f"Error calculating next fishing week: {e}")
            return 1, 1
        finally:
            session.close()
