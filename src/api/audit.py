from fastapi  import APIRouter, Depends
from pydantic import BaseModel
from src.api  import auth
from src      import database as db
import math
import sqlalchemy


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.get("/inventory")
def get_inventory():
    """ """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = result.first()
    
    return {"number_of_potions": {row1.num_red_potions + row1.num_blue_potions + row1.num_green_potions}, "ml_in_barrels": {row1.num_red_ml}, "gold": {row1.gold}}


class Result(BaseModel):
    gold_match:    bool
    barrels_match: bool
    potions_match: bool


@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """

    print(audit_explanation)

    return "OK"
