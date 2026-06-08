from pydantic import field_validator


def null_str_validator(*field_names: str):
    @field_validator(*field_names, mode="before")
    @classmethod
    def _coerce_null_strings(cls, v):
        if v == "null":
            return None
        return v

    return _coerce_null_strings
