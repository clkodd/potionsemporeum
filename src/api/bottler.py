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

    red_potions = 0
    green_potions = 0
    blue_potions = 0

    for potion in potions_delivered:
        if potion.potion_type[0] == 100:    # red
            red_potions += potion.quantity
        elif potion.potion_type[1] == 100:  # green
            green_potions += potion.quantity
        elif potion.potion_type[2] == 100:  # blue
            blue_potions += potion.quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :new_red_potions, \
                                                                        num_green_potions = :new_green_potions, \
                                                                        num_blue_potions = :new_blue_potions"), \
                                                                      {"new_red_potions": row1.num_red_potions + red_potions, \
                                                                       "new_green_potions": row1.num_green_potions + green_potions, \
                                                                       "new_blue_potions": row1.num_blue_potions + blue_potions})

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :new_red_ml, \
                                                                        num_green_ml = :new_green_ml, \
                                                                        num_blue_ml = :new_blue_ml"), \
                                                                      {"new_red_ml": row1.num_red_ml - red_potions * 100, \
                                                                       "new_green_ml": row1.num_green_ml - green_potions * 100, \
                                                                       "new_blue_ml": row1.num_blue_ml - blue_potions * 100})

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into respective potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

    plan = []

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
