from fastapi import APIRouter
import sqlalchemy
from src import database as db

"""
insert SQL commands as: 

with db.engine.begin() as connection:
        result = connection.execute(sql_to_execute)
"""

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        result = connection.execute("SELECT num_red_potions FROM global_inventory")

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": result[0],
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
