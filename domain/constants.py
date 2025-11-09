from datetime import datetime
from enum import Enum

MIN_YEAR = 1888
CURRENT_YEAR = datetime.utcnow().year


class Status(str, Enum):
    TODO = "todo"
    WATCHING = "watching"
    DONE = "done"

    def __str__(self) -> str:
        return str(self.value)


class Genre(str, Enum):
    ACTION = "action"
    ADVENTURE = "adventure"
    COMEDY = "comedy"
    DRAMA = "drama"
    FANTASY = "fantasy"
    HORROR = "horror"
    ROMANCE = "romance"
    SCI_FI = "sci-fi"
    THRILLER = "thriller"
    DOCUMENTARY = "documentary"

    def __str__(self) -> str:
        return str(self.value)


ALLOWED_KINDS = {"movie", "series"}
ALLOWED_GENRES = {g.value for g in Genre}
