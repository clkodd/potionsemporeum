from fastapi import APIRouter
import sqlalchemy
from src import database as db


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    Can return a max of 20 items.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": row1.num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
