from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    return [
            {
                "sku": "RED_POTION",
                "name": "red potion",
                "quantity": 5,
                "price": 3,
                "potion_type": [100, 0, 0, 0],
            },
            {
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": 3,
                "price": 7,
                "potion_type": [0, 100, 0, 0],
            }
        ]