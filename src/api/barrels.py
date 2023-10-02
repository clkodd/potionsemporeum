from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold"), {"new_gold": row1[2] - barrels_delivered[0].price})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :new_red_ml"), {"new_red_ml": row1[1] + barrels_delivered[0].ml_per_barrel})

    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ 
    Gets called once a day
    """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

        # row1[0] = num_red_potions, [1] = num_red_ml, [2] = gold
        
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            #if ((row1.num_red_potions) < 10) and (row1.gold >= barrel.price):
            if ((row1[0] < 10) and (row1[2] >= barrel.price)):
                return [
                    {
                        "sku": "SMALL_RED_BARREL",
                        "quantity": 1,
                    }
                ]
"""
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_RED_BARREL":
                price1 = barrel.price
                skew = barrel.skew
                print("PRICE:")
                print(price1)
                print("SKU:")
                print(skew)

        print("GOLD: ")
        print(row1[2])
        print("POTS:")
        print(row1[0])

    if ((row1[0] < 10) and (row1[2] >= price1)):
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
        """
                
