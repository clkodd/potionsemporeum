from fastapi  import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
import sqlalchemy


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    
    with db.engine.begin() as connection:   
        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory
                            SET red_ml = 0,
                            blue_ml = 0,
                            green_ml = 0,
                            dark_ml = 0,
                            gold = 100
                            """))

        connection.execute(
            sqlalchemy.text("""
                            UPDATE potion_mixes 
                            SET quantity = 0
                            """))

        connection.execute(
            sqlalchemy.text("""
                            TRUNCATE TABLE carts
                            RESTART IDENTITY
                            CASCADE
                            """))

        connection.execute(
            sqlalchemy.text("""
                            TRUNCATE TABLE account_transactions
                            RESTART IDENTITY
                            """))

        connection.execute(
            sqlalchemy.text("""
                            TRUNCATE TABLE account_ledger_entries
                            RESTART IDENTITY
                            """))

        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_ledger_entries (account_id, account_transaction_id, change) 
                                VALUES (:gold_id, :transaction_id, :start)
                                """),
                               {"gold_id": 1,
                                "transaction_id": trans_id,
                                "start": 100})

        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_transactions (description) 
                                VALUES ('Initial 100 gold')
                                """))
    
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Potions Emporeum",
        "shop_owner": "Caroline Koddenberg",
    }

