from fastapi  import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
import sqlalchemy


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
    global cartIDBase
    cartIDBase = cartIDBase + 1
    Carts[cartIDBase] = [new_cart.customer, []]

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

    for pair in curr_items:
        if item_sku in pair:
            pair[1] += cart_item.quantity
    else:
        curr_items.append([item_sku, cart_item.quantity])

    Carts[cart_id] = [Carts[cart_id][0], curr_items]

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    cost = 0
    num_reds = 0
    num_greens = 0
    num_blues = 0

    for potion_item in Carts[cart_id][1]:   # operates on the list of lists: items are [potion sku, quantity]
        if "RED" in potion_item[0]:
            cost += potion_item[1] * 5
            num_reds += potion_item[1]
        elif "GREEN" in potion_item[0]:
            cost += potion_item[1] * 50
            num_greens += potion_item[1]
        elif "BLUE" in potion_item[0]:
            cost += potion_item[1] * 50
            num_blues += potion_item[1]

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold"), {"new_gold": row1.gold + cost})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :new_red_potions, \
                                                                        num_green_potions = :new_green_potions, \
                                                                        num_blue_potions = :new_blue_potions"), \
                                                                      {"new_red_potions": row1.num_red_potions - num_reds, \
                                                                       "new_green_potions": row1.num_green_potions - num_greens, \
                                                                       "new_blue_potions": row1.num_blue_potions - num_blues})
    
    del Carts[cart_id]

    print("REDS sold: " + str(num_reds) + "\n GREENS sold: " + str(num_greens) + "\n BLUES sold: " + str(num_blues))

    return {"total_potions_bought": num_reds + num_greens + num_blues, "total_gold_paid": cost}
