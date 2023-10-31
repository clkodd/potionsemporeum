from fastapi  import APIRouter, Depends
from enum     import Enum
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
import sqlalchemy


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    with db.engine.begin() as connection:

        for potion in potions_delivered:
            potion_name = connection.execute(
                            sqlalchemy.text("""
                                            SELECT potion_id, sku
                                            FROM potion_mixes 
                                            WHERE formula = :potion_type
                                            """),
                                           {"potion_type": potion.potion_type})
            potion_name = potion_name.first()

            new_row = connection.execute(
                        sqlalchemy.text("""
                                        INSERT INTO account_transactions (description) 
                                        VALUES ('Made :quantity ':potion' (recipe :mls)')
                                        RETURNING transaction_id
                                        """),
                                       {"quantity": potion.quantity,
                                        "potion": potion_name.sku,
                                        "mls": potion.potion_type})
            trans_id = new_row.scalar()

            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_ledger_entries (account_id, account_transaction_id, change) 
                                VALUES (:potion_id, :transaction_id, :potions_made),
                                (3, :transaction_id, :red_used),
                                (4, :transaction_id, :green_used),
                                (5, :transaction_id, :blue_used),
                                (2, :transaction_id, :dark_used)
                                """),
                               {"potion_id": potion_name.potion_id + 5,
                                "transaction_id": trans_id,
                                "potions_made": potion.quantity,
                                "red_used": potion.potion_type[0] * potion.quantity * -1,
                                "green_used": potion.potion_type[1] * potion.quantity * -1,
                                "blue_used": potion.potion_type[2] * potion.quantity * -1,
                                "dark_used": potion.potion_type[3] * potion.quantity * -1})

    return "OK"


@router.post("/plan")
def get_bottle_plan():
    """ """
    with db.engine.begin() as connection:
        gold = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = 1
                                    """))
        gold = gold.first()

        red = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = 3
                                    """))
        red = red.first()

        green = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = 4
                                    """))
        green = green.first()

        blue = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = 5
                                    """))
        blue = blue.first()

        dark = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS balance
                                    FROM account_ledger_entries
                                    WHERE account_id = 2
                                    """))
        dark = dark.first()

        red = 0 if red.balance == None else red.balance
        green = 0 if green.balance == None else green.balance
        blue = 0 if blue.balance == None else blue.balance
        dark = 0 if dark.balance == None else dark.balance

        curr_mls = [red, green, blue, dark]

        formulas = connection.execute(
                        sqlalchemy.text("""
                                        SELECT formula
                                        FROM potion_mixes
                                        """))

        potions = connection.execute(
                    sqlalchemy.text("""
                                    SELECT SUM(change) AS num
                                    FROM account_ledger_entries
                                    WHERE account_id > 5
                                    """))
        num_potions = potions.first()
        space_left = 300 if num_potions.num == None else 300 - num_potions.num
       
        formula_list = [row[0] for row in formulas]
        intermediate_plan = {}

        potion_added = True
        while potion_added:
            potion_added = False

            for formula in formula_list:
                make = True

                for i in range(4):
                    if curr_mls[i] < formula[i]:
                        make = False

                if make and space_left > 1:
                    if str(formula) in intermediate_plan:
                        intermediate_plan[str(formula)] += 1
                    else:
                        intermediate_plan[str(formula)] = 1

                    for i in range(4):
                        curr_mls[i] -= formula[i]
                        
                    potion_added = True
                    space_left -= 1

        plan = []            
        
        for formula in intermediate_plan.keys():
            plan.append(
                {
                    "potion_type": eval(formula),
                    "quantity": intermediate_plan[formula]
                }
            )

        print(plan)
        return plan
