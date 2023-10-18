from fastapi  import APIRouter, Depends
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
import math
import sqlalchemy


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.get("/inventory")
def get_inventory():
    """ """

    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_mixes"))
        test = connection.execute(
                    sqlalchemy.text("""
                                    SELECT sku, name, formula, price, quantity 
                                    FROM potion_mixes 
                                    WHERE quantity > 0
                                    ORDER BY quantity DESC
                                    """))

        queries = []
        print(test)
        for row in test:
            queries.append(row)
        print(queries)


        row1 = result.first()
        
        total_potions = 0
        for row in potions:
            total_potions += row.quantity
            
        mls = row1.red_ml + row1.blue_ml + row1.green_ml + row1.dark_ml
        
        return {"number_of_potions": total_potions, "ml_in_barrels": mls, "gold": row1.gold}


class Result(BaseModel):
    gold_match:    bool
    barrels_match: bool
    potions_match: bool


@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """

    print(audit_explanation)

    return "OK"
