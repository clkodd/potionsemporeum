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
                                        SELECT formula 
                                        FROM potion_mixes
                                        """))

        row1 = ml_inventory.first()

        curr_red_ml = row1.red_ml
        curr_green_ml = row1.green_ml
        curr_blue_ml = row1.blue_ml
        curr_dark_ml = row1.dark_ml

        plan = []

        if curr_red_ml >= 50 and curr_blue_ml >= 50:
            quant = min(curr_red_ml // 50, curr_blue_ml // 50)
            if quant > 0:
                plan.append(
                    {
                        "potion_type": [50, 0, 50, 0],
                        "quantity": quant
                    }
                )
                curr_red_ml -= quant * 50
                curr_blue_ml -= quant * 50
        
        if curr_red_ml >= 100:
            quant = curr_red_ml // 100
            if quant > 0:
                plan.append(
                    {
                        "potion_type": [100, 0, 0, 0],
                        "quantity": quant,
                    }
                )
                curr_red_ml -= quant * 100

        if curr_green_ml >= 100:
            quant = curr_green_ml // 100
            if quant > 0:
                plan.append(
                    {
                        "potion_type": [0, 100, 0, 0],
                        "quantity": quant,
                    }
                )
                curr_green_ml -= quant * 100

        if curr_blue_ml >= 100:
            quant = curr_blue_ml // 100
            if quant > 0:
                plan.append(
                    {
                        "potion_type": [0, 0, 100, 0],
                        "quantity": quant,
                    }
                )
                curr_blue_ml -= quant * 100

        return plan

        # at_least_one = True

        # while at_least_one:
        #     at_least_one = False
        #     for mix in formulas:
        #         make = True
        #         for i in range(len(mix)):
        #             if curr_mls[i] < mix[i]:
        #                 make = False
        #         if make:
        #             plan.append(
        #                 {
        #                     "potion_type": mix,
        #                     "quantity": row1.num_green_ml // 100,
        #                 }
        #             )
        #             at_least_one = True

        # return plan
        

"""

#while 
            #for mix in formulas:



    if row1.num_red_ml >= 100:
        plan.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": row1.num_red_ml // 100,
            }
        )
    if row1.num_green_ml >= 100:
        plan.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": row1.num_green_ml // 100,
            }
        )
    if row1.num_blue_ml >= 100:
        plan.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": row1.num_blue_ml // 100,
            }
        )

    return plan
    """
