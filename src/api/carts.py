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


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """

    with db.engine.begin() as connection:
        new_row = connection.execute(
                    sqlalchemy.text("""
                                    INSERT INTO carts (customer)
                                    VALUES (:customer_str)
                                    RETURNING cart_id
                                    """),
                                   {"customer_str": new_cart.customer})

    return {"cart_id": new_row.scalar()}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    with db.engine.begin() as connection:
        cart = connection.execute(
                    sqlalchemy.text("""
                                    SELECT * 
                                    FROM carts
                                    WHERE cart_id = :given_id
                                    """),
                                   {"given_id": cart_id})

        row = cart.first()

    return {
        "cart_id": row.cart_id,
        "customer": row.customer
    }


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""
                            INSERT INTO cart_items (cart_id, quantity, potion_id)
                            SELECT :given_cart, :quantity, potion_mixes.potion_id
                            FROM potion_mixes
                            WHERE potion_mixes.sku = :item_sku
                            """),
                            {"given_cart": cart_id,
                            "quantity": cart_item.quantity,
                            "item_sku": item_sku})
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    cost = 0
    total_potions = 0

    with db.engine.begin() as connection:
        cart = connection.execute(
                    sqlalchemy.text("""
                                    SELECT *
                                    FROM cart_items
                                    WHERE cart_id = :given_cart_id
                                    JOIN potion_mixes
                                    ON cart_items.potion_id = potion_mixes.potion_id
                                    """),
                                    {"given_cart_id": cart_id})

        for row in cart:
            cost += row.price * row.quantity
            total_potions += row.quantity

            print("\ncart id: {} / item sku: {} / quantity: {}\n".format(cart_id, row.sku, row.quantity))

            connection.execute(
                    sqlalchemy.text("""
                                    UPDATE potion_mixes
                                    SET quantity = quantity - :num_sold
                                    WHERE potion_id = :row_potion_id
                                    """),
                                   {"num_sold": row.quantity,
                                    "row_potion_id": row.potion_id})
        
        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory 
                            SET gold = gold + :cost
                            """),
                           {"cost": cost})

        print("\ncart id:{} / cost: {}\n".format(cart_id, cost))
        
    return {"total_potions_bought": total_potions, "total_gold_paid": cost}

    #         cost += row.quantity * 
    #         connection.execute(
    #             sqlalchemy.text("""
    #                             SELECT *
    #                             FROM cart_items
    #                             WHERE cart_id = :given_cart_id
    #                             """),
    #                             {"given_cart_id": cart_id})


    # for row in cart:
    #     if "RED" in row.:
    #         cost += potion_item[1] * 50
    #         num_reds += potion_item[1]
    #     elif "GREEN" in potion_item[0]:
    #         cost += potion_item[1] * 50
    #         num_greens += potion_item[1]
    #     elif "BLUE" in potion_item[0]:
    #         cost += potion_item[1] * 50
    #         num_blues += potion_item[1]
    #     elif "PURPLE" in potion_item[0]:
    #         cost += potion_item[1] * 50
    #         num_purples += potion_item[1]
    
    # with db.engine.begin() as connection:

    #     for potion_item in Carts[cart_id][1]:
    #         connection.execute(
    #             sqlalchemy.text("""
    #                             UPDATE potion_mixes 
    #                             SET quantity = quantity + :num_bought
    #                             WHERE sku = :sku
    #                             """),
    #                             {"num_bought": potion_item[1], 
    #                             "sku": potion_item[0]})

    
