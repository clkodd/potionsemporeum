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

    # cost = 0
    # new_red_ml = 0
    # new_green_ml = 0
    # new_blue_ml = 0
    # new_dark_ml = 0

    # for barrel in barrels_delivered:
    #     cost += barrel.price * barrel.quantity
    #     if "RED" in barrel.sku:
    #         new_red_ml += barrel.ml_per_barrel * barrel.quantity
    #     elif "GREEN" in barrel.sku:
    #         new_green_ml += barrel.ml_per_barrel * barrel.quantity
    #     elif "BLUE" in barrel.sku:
    #         new_blue_ml += barrel.ml_per_barrel * barrel.quantity
    #     elif "DARK" in barrel.sku:
    #         new_dark_ml += barrel.ml_per_barrel * barrel.quantity

    # with db.engine.begin() as connection:
    #     connection.execute(
    #         sqlalchemy.text("""
    #                         UPDATE global_inventory 
    #                         SET gold = gold - :cost,
    #                         red_ml = red_ml + :new_red_ml,
    #                         green_ml = green_ml + :new_green_ml,
    #                         blue_ml = blue_ml + :new_blue_ml,
    #                         dark_ml = dark_ml + :new_dark_ml
    #                         """),
    #                        {"cost": cost,
    #                         "new_red_ml": new_red_ml,
    #                         "new_green_ml": new_green_ml,
    #                         "new_blue_ml": new_blue_ml,
    #                         "new_dark_ml": new_dark_ml})

    for barrel in barrels_delivered:
        with db.engine.begin() as connection:
            new_row = connection.execute(
                        sqlalchemy.text("""
                                        INSERT INTO account_transactions (description) 
                                        VALUES ('Purchased :quantity ':barrel_sku' (total :mls mL, :cost gold)')
                                        RETURNING transaction_id
                                        """),
                                       {"quantity": barrel.quantity,
                                        "barrel_sku": barrel.sku,
                                        "mls": barrel.ml_per_barrel * barrel.quantity,
                                        "cost": barrel.price * barrel.quantity})

            trans_id = new_row.scalar()

            if "RED" in barrel.sku:
                ml_account_num = 3
            elif "GREEN" in barrel.sku:
                ml_account_num = 4
            elif "BLUE" in barrel.sku:
                ml_account_num = 5
            else:
                ml_account_num = 2
                
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_ledger_entries (account_id, account_transaction_id, change) 
                                VALUES (:gold_id, :transaction_id, :cost),
                                (:color_id, :transaction_id, :added_mls)
                                """),
                               {"gold_id": 1,
                                "transaction_id": trans_id,
                                "cost": barrel.price * barrel.quantity * -1,
                                "color_id": ml_account_num,
                                "added_mls": barrel.ml_per_barrel * barrel.quantity})

    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ 
    Gets called once a day
    """

    print(wholesale_catalog)

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

    reds = [red.balance, "RED"]
    greens = [green.balance, "GREEN"]
    blues = [blue.balance, "BLUE"]
    potions = [reds, greens, blues]

    running_gold = gold.balance

    if "LARGE" in wholesale_catalog[0].sku and running_gold > 1500:
        size = "LARGE"
    elif "MEDIUM" in wholesale_catalog[0].sku and running_gold > 800:
        size = "MEDIUM"
    else:
        size = "SMALL"

    plan = []

    for barrel in wholesale_catalog:
        if "DARK" in barrel.sku:
            quant = running_gold // barrel.price if barrel.quantity >= running_gold // barrel.price else barrel.quantity
            if running_gold >= barrel.price * quant and quant > 0:
                plan.append(
                            {
                                "sku": barrel.sku,
                                "quantity": quant,
                            }
                )
                running_gold -= barrel.price * quant

    for i in range(3):
        buy_set = min(potions)
        buy_color = buy_set[1]

        for barrel in wholesale_catalog:
            if buy_color in barrel.sku and size in barrel.sku:
                quant = running_gold // barrel.price // len(potions) if running_gold // barrel.price >= len(potions) else running_gold // barrel.price
                quant = quant if barrel.quantity >= quant else barrel.quantity
                if running_gold >= barrel.price * quant and quant > 0:
                    plan.append(
                                {
                                    "sku": barrel.sku,
                                    "quantity": quant,
                                }
                    )
                    running_gold -= barrel.price * quant

        potions.remove(buy_set)
    
    return plan
