import pydantic


class Dish(pydantic.BaseModel):
    name: str
    description: str
    price: int
    photo: str

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "photo": self.photo
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            photo=data['photo']
        )