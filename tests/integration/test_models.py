import pytest
from app.domain.models import Server, StoreAccount, GameAccount, Character, DailyCorActivity, CharacterType

def test_relationships(test_db):
    # Create Server
    server = Server(name="IntegrationServer")
    test_db.add(server)
    test_db.commit()
    
    # Create Store
    store = StoreAccount(email="integration@store.com")
    test_db.add(store)
    test_db.commit()
    
    # Create Game Account linked to Store and Server
    game_acc = GameAccount(username="IntegrationUser", store_account_id=store.id, server_id=server.id)
    test_db.add(game_acc)
    test_db.commit()
    
    # Check relationships
    assert game_acc.store_account == store
    assert game_acc.server == server
    assert server.game_accounts[0] == game_acc
    assert store.game_accounts[0] == game_acc
    
    # Create Character
    char = Character(name="IntegrationChar", game_account_id=game_acc.id, char_type=CharacterType.FISHERMAN)
    test_db.add(char)
    test_db.commit()
    
    assert char.game_account == game_acc
    assert game_acc.characters[0] == char
    assert char.char_type == CharacterType.FISHERMAN

def test_cascade_delete_behavior(test_db):
    """Ensure we understand delete behavior (even if cascade not strictly enforced by SQLITE in memory without pragma)"""
    # Just verifying ORM behavior
    pass
