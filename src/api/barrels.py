from fastapi  import APIRouter, Depends
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
import sqlalchemy


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

# buy a red barrel first
# last_barrel_purchased = "GREEN"


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    cost = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0

    for barrel in barrels_delivered:
        cost += barrel.price * barrel.quantity
        if "RED" in barrel.sku:
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif "GREEN" in barrel.sku:
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif "BLUE" in barrel.sku:
            blue_ml += barrel.ml_per_barrel * barrel.quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold"), {"new_gold": row1.gold - cost})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :new_red_ml, \
                                                                        num_green_ml = :new_green_ml, \
                                                                        num_blue_ml = :new_blue_ml"), \
                                                                      {"new_red_ml": row1.num_red_ml + red_ml, \
                                                                       "new_green_ml": row1.num_green_ml + green_ml, \
                                                                       "new_blue_ml": row1.num_blue_ml + blue_ml})

    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ 
    Gets called once a day
    """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

    plan = []

    reds = [row1.num_red_potions, row1.num_red_ml, "RED"]
    greens = [row1.num_green_potions, row1.num_green_ml, "GREEN"]
    blues = [row1.num_blue_potions, row1.num_blue_ml, "BLUE"]

    buy_color = min(reds, greens, blues)[1]

    for barrel in wholesale_catalog:
        if buy_color in barrel.sku and row1.gold >= barrel.price:
            plan.append(
                        {
                            "sku": barrel.sku,
                            "quantity": row1.gold // barrel.price,
                        }
            )

    return plan

    """
        if barrel.sku == "SMALL_RED_BARREL":
                if ((row1.num_red_potions < 10) and (row1.gold >= barrel.price)):
                    plan.append(
                        {
                            "sku": "SMALL_RED_BARREL",
                            "quantity": 1,
                        }
                    )
    -----

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_GREEN_BARREL" and last_barrel_purchased == "BLUE" and row1.gold >= barrel.price:
            plan.append(
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": row1.gold // barrel.price,
                }
            )
            last_barrel_purchased = "GREEN"
            return plan
        elif barrel.sku == "SMALL_RED_BARREL" and last_barrel_purchased == "GREEN" and row1.gold >= barrel.price:
            plan.append(
                {
                    "sku": "SMALL_RED_BARREL",
                    "quantity": row1.gold // barrel.price,
                }
            )
            last_barrel_purchased = "RED"
            return plan
        elif barrel.sku == "SMALL_BLUE_BARREL" and last_barrel_purchased == "RED" and row1.gold >= barrel.price:
            plan.append(
                {
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": row1.gold // barrel.price,
                }
            )
            last_barrel_purchased = "BLUE"
            return plan

    return plan
"""