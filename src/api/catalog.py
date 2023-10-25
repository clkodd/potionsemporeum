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
                                    SELECT potion_id, sku, name, formula, price 
                                    FROM potion_mixes
                                    """))

    catalog = []
    potions_in_catalog = 0

    for row in potions:
        if potions_in_catalog == 6:
            print(catalog)
            return catalog

        with db.engine.begin() as connection:
            quant = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = :potion_id
                                    """),
                                   {"potion_id": row.potion_id})
            quant = quant.first()

        catalog.append(
            {
                "sku": row.sku,
                "name": row.name,
                "quantity": quant.balance,
                "price": row.price,
                "potion_type": row.formula
            }
        )
        potions_in_catalog += 1

    return catalog
