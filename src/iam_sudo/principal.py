#
# Copyright 2021 - binx.io B.V.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click

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

    @staticmethod
    def click_option(ctx, param, value):
        if value is not None:
            try:
                return Principal.create_from_string(value)
            except ValueError as e:
                raise click.UsageError(f"{e}, expected format <class>:<identity>", ctx)