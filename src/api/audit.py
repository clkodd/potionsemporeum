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
        #red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        #red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        #gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        results = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row1 = results.first()

    print(f"goldD {row1.gold}")
    print(f"red ml {row1.red_ml}")
    
    return {"number_of_potions": {row1.red_potions}, "ml_in_barrels": {row1.red_ml}, "gold": {row1.gold}}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
