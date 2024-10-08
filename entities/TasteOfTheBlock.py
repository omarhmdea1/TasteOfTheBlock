import pydantic

from entities.Restaurant import Restaurant


class TasteOfTheBlock(pydantic.BaseModel):
    restaurants: list[Restaurant]
