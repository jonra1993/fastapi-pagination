from typing import Any

import uvicorn
from beanie import Document, init_beanie
from faker import Faker
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

from fastapi_pagination import LimitOffsetPage, CustomPage, Page, add_pagination
from fastapi_pagination.ext.beanie import paginate

faker = Faker()


class UserIn(Document):
    name: str = Field(..., example=faker.name())
    email: str = Field(..., example=faker.email())

    class Settings:
        name = "users"


class UserOut(UserIn):
    _id: int


app = FastAPI()
client: AsyncIOMotorClient


@app.on_event("startup")
async def on_startup() -> None:
    global client
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(client.test, document_models=[UserIn])

    users = [UserIn(name=faker.name(), email=faker.email()) for _ in range(100)]
    await UserIn.insert_many(users)


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    result = await user_in.insert()
    return await UserIn.find_one(UserIn.id == result.id)


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
@app.get("/users/custom-page", response_model=CustomPage[UserOut])
async def get_users() -> Any:
    return await paginate(UserIn)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_beanie:app")
