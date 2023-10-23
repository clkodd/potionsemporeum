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

        # result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_mixes"))
        # row1 = result.first()
        
        # total_potions = 0
        # for row in potions:
        #     total_potions += row.quantity
            
        # mls = row1.red_ml + row1.blue_ml + row1.green_ml + row1.dark_ml

        potions = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS num
                                    FROM account_ledger_entries
                                    WHERE account_id > 5
                                    """))
        potions = potions.first()

        mls = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS total
                                    FROM account_ledger_entries
                                    WHERE account_id BETWEEN 2 AND 5
                                    """))
        mls = mls.first()

        gold = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = 1
                                    """))
        gold = gold.first()

        
        # print("GOLD TOTAL: {}".format(gold.balance))
        
        return {"number_of_potions": potions.num, "ml_in_barrels": mls.total, "gold": gold.balance}


class Result(BaseModel):
    gold_match:    bool
    barrels_match: bool
    potions_match: bool


@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """

    print(audit_explanation)

    return "OK"
