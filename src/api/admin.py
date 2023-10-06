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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()
    
        for col in row1:
                #connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100, num_red_ml = 0, num_red_potions = 0"))
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET :column = 0"), {"column": col})
                
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100"))
    #with db.engine.begin() as connection:
            #connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100"))
    
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Potions Emporeum",
        "shop_owner": "Caroline Koddenberg",
    }

