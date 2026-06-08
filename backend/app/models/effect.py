from sqlmodel import Field, SQLModel


class Effect(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    category: str = Field()
    description: str = Field()
    library: str = Field()
    doc_path: str | None = Field(default=None)
