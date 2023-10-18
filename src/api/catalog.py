from fastapi import APIRouter
from src     import database as db
import sqlalchemy


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    Can return a max of 20 items.
    """

    with db.engine.begin() as connection:
        potions = connection.execute(
                    sqlalchemy.text("""
                                    SELECT sku, name, formula, price, quantity 
                                    FROM potion_mixes 
                                    WHERE quantity > 0
                                    ORDER BY quantity DESC
                                    """))

    catalog = []

    # if len(potions) > 6:    # sell the 6 potions with the most quantity
    #     sorted_potions = sorted(potions, key = lambda row: row.quantity)
    #     top_six = sorted_potions[:6]
    # else:
    #     top_six = potions

    # top_six = potions
    potions_in_catalog = 0

    for row in potions:
        if potions_in_catalog == 6:
            print(catalog)
            return catalog
        catalog.append(
            {
                "sku": row.sku,
                "name": row.name,
                "quantity": row.quantity,
                "price": row.price,
                "potion_type": row.formula
            }
        )
        potions_in_catalog += 1

    # print(catalog)
    # return catalog
