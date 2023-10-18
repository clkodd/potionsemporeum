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

        red_ml_used = sum(potion.quantity * potion.potion_type[0] for potion in potions_delivered)
        green_ml_used = sum(potion.quantity * potion.potion_type[1] for potion in potions_delivered)
        blue_ml_used = sum(potion.quantity * potion.potion_type[2] for potion in potions_delivered)
        dark_ml_used = sum(potion.quantity * potion.potion_type[3] for potion in potions_delivered)

        for potion in potions_delivered:
            connection.execute(
                sqlalchemy.text("""
                                UPDATE potion_mixes 
                                SET quantity = quantity + :num_made
                                WHERE formula = :potion_type
                                """),
                               {"num_made": potion.quantity, 
                                "potion_type": potion.potion_type})
        
        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory
                            SET red_ml = red_ml - :red_ml_used,
                            green_ml = green_ml - :green_ml_used,
                            blue_ml = blue_ml - :blue_ml_used,
                            dark_ml = dark_ml - :dark_ml_used
                            """),
                           {"red_ml_used": red_ml_used,
                            "green_ml_used": green_ml_used,
                            "blue_ml_used": blue_ml_used,
                            "dark_ml_used": dark_ml_used})

    return "OK"


@router.post("/plan")
def get_bottle_plan():
    """ """
    with db.engine.begin() as connection:
        ml_inventory = connection.execute(
                            sqlalchemy.text("""
                                            SELECT * 
                                            FROM global_inventory
                                            """))

        formulas = connection.execute(
                        sqlalchemy.text("""
                                        SELECT formula, quantity 
                                        FROM potion_mixes
                                        ORDER BY quantity DESC
                                        """))

        row1 = ml_inventory.first()
        formula_list = [row[0] for row in formulas]
        curr_mls = [row1.red_ml, row1.green_ml, row1.blue_ml, row1.dark_ml]
        intermediate_plan = {}

        potion_added = True
        while potion_added:
            potion_added = False
            for formula in formula_list:
                make = True
                for i in range(4):
                    if curr_mls[i] < formula[i]:
                        make = False
                if make:
                    if str(formula) in intermediate_plan:
                        intermediate_plan[str(formula)] += 1
                    else:
                        intermediate_plan[str(formula)] = 1
                    for i in range(4):
                        curr_mls[i] -= formula[i]
                    potion_added = True

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
