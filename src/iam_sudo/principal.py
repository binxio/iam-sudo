class Principal(object):
    def __init__(self, typ: str, identifier: str):
        self.typ = typ
        self.identifier = identifier

    def __repr__(self):
        return f"{self.typ}:{self.identifier}"

    def __eq__(self, other):
        return self.typ == other.typ and self.identifier == other.identifier

    @staticmethod
    def create_from_dict(d: dict) -> "Principal":
        if "type" in d and "identifier" in d:
            return Principal(d.get("type"), d.get("identifier"))
        raise ValueError("dictionary is missing type and/or identifier")

    @staticmethod
    def create_from_string(s: str) -> "Principal":
        parts = s.split(":", maxsplit=2)
        if len(parts) != 2:
            raise ValueError(f"{s} is not a string principal notation")
        return Principal(parts[0], parts[1])
