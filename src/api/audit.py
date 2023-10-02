from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db


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

        # row1[0] = num_red_potions, [1] = num_red_ml, [2] = gold
    
    return {"number_of_potions": {row1[0]}, "ml_in_barrels": {row1[1]}, "gold": {row1[2]}}


class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool


@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ 
    Gets called once a day 
    """
    print(audit_explanation)

    return "OK"
