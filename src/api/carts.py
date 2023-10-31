from fastapi  import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
from enum     import Enum
import sqlalchemy


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "0",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    query = """
            SELECT carts.customer AS customer,
                   cart_items.quantity AS quantity,
                   potion_mixes.name AS potion, 
                   account_transactions.transaction_id AS id,
                   account_transactions.created_at AS time,
                   account_ledger_entries.change AS cost
            FROM carts
            JOIN cart_items
                ON carts.cart_id = cart_items.cart_id
            JOIN potion_mixes
                ON cart_items.potion_id = potion_mixes.potion_id
            JOIN account_transactions
                ON carts.cart_id = account_transactions.cart_id
            JOIN account_ledger_entries
                ON account_transactions.transaction_id = account_ledger_entries.account_transaction_id
                WHERE account_id = 1
            ORDER BY customer"""
    
    with db.engine.begin() as connection:
        results = connection.execute(
                        sqlalchemy.text("""
                                                SELECT carts.customer AS customer,
                                                    cart_items.quantity AS quantity,
                                                    account_transactions.transaction_id AS id,
                                                    account_transactions.created_at AS time
                                                FROM carts
                                                JOIN cart_items
                                                    ON carts.cart_id = cart_items.cart_id
                                                JOIN account_transactions
                                                    ON carts.cart_id = account_transactions.cart_id
                                            
                                                ORDER BY customer""")).all()

    print(results)
    print(len(results))
    return 0

    if sort_col is search_sort_options.customer_name:
        query += "customer"
    elif sort_col is search_sort_options.item_sku:
        query += "potion"
    elif sort_col is search_sort_options.line_item_total:
        query += "cost"
    elif sort_col is search_sort_options.timestamp:
        query += "time"
    else:
        assert False

    if sort_order is search_sort_order.desc:
        query += " DESC"

    search_page = int(search_page)
    
    offset = str(search_page * 5)
    query += "\nLIMIT 5\nOFFSET " + offset

    with db.engine.begin() as connection:
        results = connection.execute(
                        sqlalchemy.text(query))

    items = []

    for row in results:
        items.append(
            {
                "line_item_id": row.id,
                "item_sku": row.potion,
                "customer_name": row.customer,
                "line_item_total": row.cost,
                "timestamp": row.time,
            }
        )

    print(items)

    prev = nextt = None
    if search_page > 1:
        prev = search_page - 1
    if len(items) > 5:
        nextt = search_page + 1

    return {
        "previous": prev,
        "next": nextt,
        "results": items,
    }



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
                                        INSERT INTO account_transactions (description, cart_id) 
                                        VALUES ('Sold :quantity ':potion_sku' (cost :cost gold)', :cart_id)
                                        RETURNING transaction_id
                                        """),
                                       {"quantity": row.quantity,
                                        "potion_sku": row.sku,
                                        "cost": row.price * row.quantity,
                                        "cart_id": cart_id})
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

    return {"total_potions_bought": total_potions, "total_gold_paid": cost}
