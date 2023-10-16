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
    
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Potions Emporeum",
        "shop_owner": "Caroline Koddenberg",
    }

