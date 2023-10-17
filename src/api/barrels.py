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
    new_red_ml = 0
    new_green_ml = 0
    new_blue_ml = 0
    new_dark_ml = 0

    for barrel in barrels_delivered:
        cost += barrel.price * barrel.quantity
        if "RED" in barrel.sku:
            new_red_ml += barrel.ml_per_barrel * barrel.quantity
        elif "GREEN" in barrel.sku:
            new_green_ml += barrel.ml_per_barrel * barrel.quantity
        elif "BLUE" in barrel.sku:
            new_blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif "DARK" in barrel.sku:
            new_dark_ml += barrel.ml_per_barrel * barrel.quantity

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory 
                            SET gold = gold - :cost,
                            red_ml = red_ml + :new_red_ml,
                            green_ml = green_ml + :new_green_ml,
                            blue_ml = blue_ml + :new_blue_ml,
                            dark_ml = dark_ml + :new_dark_ml
                            """),
                           {"cost": cost,
                            "new_red_ml": new_red_ml,
                            "new_green_ml": new_green_ml,
                            "new_blue_ml": new_blue_ml,
                            "new_dark_ml": new_dark_ml})

    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ 
    Gets called once a day
    """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(
                    sqlalchemy.text("""
                                    SELECT * 
                                    FROM global_inventory
                                    """))
        row1 = result.first()

    plan = []

    reds = [row1.red_ml, "RED"]
    greens = [row1.green_ml, "GREEN"]
    blues = [row1.blue_ml, "BLUE"]

    potions = [reds, greens, blues]
    buy_set1 = min(potions)
    buy_color1 = buy_set1[1]

    running_gold = row1.gold

    if "LARGE" in wholesale_catalog[0].sku and row1.gold > 1500:
        size = "LARGE"
    elif "MEDIUM" in wholesale_catalog[0].sku and row1.gold > 800:
        size = "MEDIUM"
    else:
        size = "SMALL"

    # for barrel in wholesale_catalog:
    #     if "DARK" in barrel.sku:
    #         quant = running_gold // barrel.price if barrel.quantity >= (running_gold // barrel.price) else barrel.quantity
    #         if running_gold >= barrel.price * quant and quant > 0:
    #             plan.append(
    #                         {
    #                             "sku": barrel.sku,
    #                             "quantity": quant,
    #                         }
    #             )
    #             running_gold -= barrel.price * quant

    for barrel in wholesale_catalog:
        if buy_color1 in barrel.sku and size in barrel.sku:
            quant = running_gold // barrel.price // 3 if running_gold // barrel.price >= 3 else running_gold // barrel.price
            quant = quant if barrel.quantity >= quant else barrel.quantity
            if running_gold >= barrel.price * quant and quant > 0:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )
                running_gold -= barrel.price * quant

    potions.remove(buy_set1)
    buy_set2 = min(potions)
    buy_color2 = buy_set2[1]

    for barrel in wholesale_catalog:
        if buy_color2 in barrel.sku and size in barrel.sku:
            quant = running_gold // barrel.price // 2 if running_gold // barrel.price >= 2 else running_gold // barrel.price
            quant = quant if barrel.quantity >= quant else barrel.quantity
            if running_gold >= barrel.price * quant and quant > 0:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )
                running_gold -= barrel.price * quant

    potions.remove(buy_set2)
    buy_set3 = min(potions)
    buy_color3 = buy_set3[1]

    for barrel in wholesale_catalog:
        if buy_color3 in barrel.sku and size in barrel.sku:
            quant = running_gold // barrel.price
            quant = quant if barrel.quantity >= quant else barrel.quantity
            if running_gold >= barrel.price * quant and quant > 0:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )

    return plan
