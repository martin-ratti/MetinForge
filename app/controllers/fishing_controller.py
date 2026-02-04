from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import Config
from app.models.models import Server, StoreAccount, GameAccount, Character, CharacterType, FishingActivity
from sqlalchemy import extract

from app.controllers.base_controller import BaseController

class FishingController(BaseController):
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
            print(f"Error updating fishing status: {e}")
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
            print(f"Error calculating next fishing week: {e}")
            return 1, 1
        finally:
            session.close()
