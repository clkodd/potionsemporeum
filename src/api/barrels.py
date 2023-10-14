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


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    cost = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0

    for barrel in barrels_delivered:
        cost += barrel.price * barrel.quantity
        if "RED" in barrel.sku:
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif "GREEN" in barrel.sku:
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif "BLUE" in barrel.sku:
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif "DARK" in barrel.sku:
            dark_ml += barrel.ml_per_barrel * barrel.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost, \
                                                                        num_red_ml = num_red_ml + :new_red_ml, \
                                                                        num_green_ml = num_green_ml + :new_green_ml, \
                                                                        num_blue_ml = num_blue_ml + :new_blue_ml, \
                                                                        num_dark_ml = num_dark_ml + :new_dark_ml"), \
                                                                      {"cost": cost, \
                                                                       "new_red_ml": red_ml, \
                                                                       "new_green_ml": green_ml, \
                                                                       "new_blue_ml": blue_ml, \
                                                                       "new_dark_ml": dark_ml})

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

    potions = [reds, greens, blues]
    buy_set1 = min(potions)
    buy_color1 = buy_set1[2]

    running_gold = row1.gold

    if "LARGE" in wholesale_catalog[0].sku:
        size = "LARGE"
    elif "MEDIUM" in wholesale_catalog[0].sku:
        size = "MEDIUM"
    else:
        size = "SMALL"

    #size = "LARGE" if "LARGE" in wholesale_catalog[0].sku else "MEDIUM"

    for barrel in wholesale_catalog:
        if "DARK" in barrel.sku and running_gold >= barrel.price:
            plan.append(
                        {
                            "sku": barrel.sku,
                            "quantity": 1,
                        }
            )
            running_gold -= barrel.price

    for barrel in wholesale_catalog:
        if buy_color1 in barrel.sku and size in barrel.sku:
            quant = running_gold // barrel.price // 3 if running_gold // barrel.price >= 3 else running_gold // barrel.price
            quant = quant if barrel.quantity >= quant else barrel.quantity
            if running_gold >= barrel.price * quant:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )
                running_gold -= barrel.price * quant

    potions.remove(buy_set1)
    buy_set2 = min(potions)
    buy_color2 = buy_set2[2]

    for barrel in wholesale_catalog:
        if buy_color2 in barrel.sku and size in barrel.sku:
            quant = running_gold // barrel.price // 2 if running_gold // barrel.price >= 2 else running_gold // barrel.price
            quant = quant if barrel.quantity >= quant else barrel.quantity
            if running_gold >= barrel.price * quant:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )
                running_gold -= barrel.price * quant

    potions.remove(buy_set2)
    buy_set3 = min(potions)
    buy_color3 = buy_set3[2]

    for barrel in wholesale_catalog:
        if buy_color3 in barrel.sku and size in barrel.sku:
            quant = running_gold // barrel.price
            quant = quant if barrel.quantity >= quant else barrel.quantity
            if running_gold >= barrel.price * quant:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )

    return plan
