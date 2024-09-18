from pydantic import BaseModel


class User(BaseModel):

    def __call__(self, user_id, name, surname):
        self.user_id = user_id
        self.name = name
        self.surname = surname



