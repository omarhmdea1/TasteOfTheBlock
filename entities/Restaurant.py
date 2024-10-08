import pydantic

from entities.Dish import Dish


class Restaurant(pydantic.BaseModel):
    name: str
    description: str
    category: str
    user_id: int
    menu: list[Dish]

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "menu": [dish.to_dict() for dish in self.menu]
        }

    @classmethod
    def from_dict(cls, data) -> 'Restaurant':
        menu = [Dish.from_dict(dish_data) for dish_data in data.get('menu', [])]
        return cls(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            user_id=data['user_id'],
            menu=menu
        )
