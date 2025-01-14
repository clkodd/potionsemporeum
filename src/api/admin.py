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
                            TRUNCATE TABLE carts
                            RESTART IDENTITY
                            CASCADE
                            """))

        connection.execute(
            sqlalchemy.text("""
                            TRUNCATE TABLE account_transactions
                            RESTART IDENTITY
                            CASCADE
                            """))

        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_transactions (description) 
                                VALUES ('Initial 100 gold')
                                """))

        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_ledger_entries (account_id, account_transaction_id, change) 
                                VALUES (1, 1, 100)
                                """))
    
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Potions Emporeum",
        "shop_owner": "Caroline Koddenberg",
    }

