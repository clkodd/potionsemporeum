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
                                    SELECT cart_items.*, potion_mixes.potion_id, potion_mixes.price, potion_mixes.sku
                                    FROM cart_items
                                    JOIN potion_mixes
                                    ON cart_items.potion_id = potion_mixes.potion_id
                                    WHERE cart_items.cart_id = :given_cart_id
                                    """),
                                   {"given_cart_id": cart_id})

        for row in cart:
            cost += row.price * row.quantity
            total_potions += row.quantity

            new_row = connection.execute(
                        sqlalchemy.text("""
                                        INSERT INTO account_transactions (description) 
                                        VALUES ('Sold :quantity ':potion_sku' (cost :cost gold)')
                                        RETURNING transaction_id
                                        """),
                                       {"quantity": row.quantity,
                                        "potion_sku": row.sku,
                                        "cost": row.price * row.quantity})
            trans_id = new_row.scalar()

            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO account_ledger_entries (account_id, account_transaction_id, change) 
                                VALUES (:gold_id, :transaction_id, :cost),
                                (:potion_id, :transaction_id, :num_sold)
                                """),
                               {"gold_id": 1,
                                "transaction_id": trans_id,
                                "cost": row.price * row.quantity,
                                "potion_id": row.potion_id + 5,
                                "num_sold": row.quantity * -1})


        #     connection.execute(
        #             sqlalchemy.text("""
        #                             UPDATE potion_mixes
        #                             SET quantity = quantity - :num_sold
        #                             WHERE potion_id = :row_potion_id
        #                             """),
        #                            {"num_sold": row.quantity,
        #                             "row_potion_id": row.potion_id})
        
        # connection.execute(
        #     sqlalchemy.text("""
        #                     UPDATE global_inventory 
        #                     SET gold = gold + :cost
        #                     """),
        #                    {"cost": cost})

    return {"total_potions_bought": total_potions, "total_gold_paid": cost}
