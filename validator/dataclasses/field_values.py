from pydantic import BaseModel


class FieldValuesDataClass(BaseModel):
    pengguna: list[str]
    judul: list[str]
    topik: list[str]
