from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


# CartID : [ Customer, [[potion_sku, quantity], [potion_sku, quantity], ...] ]
Carts = {}
cartIDBase = 0

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    cartIDBase += 1
    Carts[cartIDBase] = [ new_cart.customer, [] ]

    return {"cart_id": cartIDBase}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    curr_cart = Carts[cart_id]

    return {
        "cart_id": cart_id,
        "customer": curr_cart[0],
        "cart": curr_cart[1]
    }


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    curr_items = Carts[cart_id][1]
    curr_items.append([item_sku, cart_item.quantity])
    Carts[cart_id] = [Carts[cart_id][0], curr_items]

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    reds_in_cart = Carts[cart_id][1][0][1]
    cost = reds_in_cart * 50

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

        # row1[0] = num_red_potions, [1] = num_red_ml, [2] = gold

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold"), {"new_gold": row1[2] + cost})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :new_red_potions"), {"new_red_potions": row1[0] - reds_in_cart})


    return {"total_potions_bought": reds_in_cart, "total_gold_paid": cost}
