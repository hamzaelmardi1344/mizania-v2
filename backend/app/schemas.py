from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
class Login(Strict):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)
class NewDossier(Strict):
    name: str = Field(min_length=2, max_length=160)
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{2,32}$")
    ice: str = Field(default="", pattern=r"^([0-9]{15})?$")
class NewExercise(Strict):
    label: str = Field(min_length=1, max_length=32)
    starts_on: date
    ends_on: date
    @model_validator(mode="after")
    def dates(self):
        if self.ends_on < self.starts_on: raise ValueError("Période invalide")
        return self
class NewAssignment(Strict):
    user_id: str
    role: Literal["manager","reviewer","collaborator","client"]
    active: bool = True
class Invite(Strict):
    name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
class AcceptInvitation(Strict):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    token: str = Field(min_length=20, max_length=128)
    password: str = Field(min_length=14, max_length=128)
class NewRequest(Strict):
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=3, max_length=4000)
class Reply(Strict):
    reply: str = Field(min_length=1, max_length=4000)
class NewVersion(Strict):
    source_id: str
    title: str = Field(min_length=5, max_length=200)
    citation: str = Field(min_length=5, max_length=200)
    url: str = Field(max_length=2000)
    text: str = Field(min_length=50, max_length=500000)
    published_on: date
    effective_from: date
    effective_to: date | None = None
    @model_validator(mode="after")
    def dates(self):
        if self.effective_to and self.effective_to < self.effective_from: raise ValueError("Période invalide")
        return self
class ReviewVersion(Strict):
    decision: Literal["verified", "rejected"]
    note: str = Field(min_length=20, max_length=4000)
