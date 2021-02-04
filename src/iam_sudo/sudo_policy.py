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
#
import os
from fnmatch import fnmatch
from io import StringIO
from re import fullmatch
from typing import List

import jsonschema
from ruamel.yaml import YAML

import iam_sudo.principal as iam_principal
from iam_sudo.roles import Role, Roles

schema = {
    "type": "object",
    "required": ["allowed-role-names", "allowed-principals", "allowed-base-roles"],
    "properties": {
        "allowed-role-names": {
            "description": "glob pattern of allowed role names",
            "type": "array",
            "items": {"type": "string"},
        },
        "allowed-principals": {
            "description": "allowed role principals",
            "type": "array",
            "items": {"type": "object"},
        },
        "allowed-base-roles": {
            "description": "allowed base roles",
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


class Policy(object):
    def __init__(self):
        self.allowed_role_names: List[str] = []
        self.allowed_principals: List[iam_principal.Principal] = []
        self.allowed_base_roles: List[str] = []

    @staticmethod
    def load(doc: str) -> "Policy":
        yaml = YAML()
        policy = yaml.load(doc)
        jsonschema.validate(policy, schema)

        result = Policy()
        result.allowed_role_names = policy["allowed-role-names"]
        result.allowed_base_roles = policy["allowed-base-roles"]
        for principal in policy["allowed-principals"]:
            for typ, identifier in principal.items():
                result.allowed_principals.append(
                    iam_principal.Principal(typ, identifier)
                )
        return result

    def is_allowed_role_name(self, role_name: str) -> bool:
        for allowed in self.allowed_role_names:
            if allowed == role_name or fnmatch(role_name, allowed):
                return True
        return False

    def is_allowed_principal(self, principal: iam_principal.Principal) -> bool:
        for allowed in self.allowed_principals:
            if fnmatch(principal.typ, allowed.typ) and fnmatch(
                principal.identifier, allowed.identifier
            ):
                return True
        return False

    def is_allowed_base_role(self, base_role: str) -> bool:
        if not fullmatch(r"arn:aws:iam:[^:]*:[0-9]+:role/.*", base_role):
            return False

        for allowed in self.allowed_base_roles:
            if fnmatch(base_role, allowed):
                return True
        return False

    def allowed_roles(self, roles: Roles) -> Roles:
        return Roles(list(filter(lambda r: self.is_allowed_role(r), roles)))

    def is_allowed_role(self, role: Role) -> bool:
        if not self.is_allowed_role_name(role.name):
            return False

        if not next(
            filter(lambda p: self.is_allowed_principal(p), role.principals), None
        ):
            return False

        return True

    def __repr__(self):
        out = StringIO()
        out.write(f"allowed-role-names:\n")
        for a in self.allowed_role_names:
            out.write(f"  - {a}\n")
        out.write(f"allowed-principals:\n")
        for a in self.allowed_principals:
            out.write(f"  - {a}\n")
        out.write(f"allowed-base-roles:\n")
        for a in self.allowed_base_roles:
            out.write(f"  - {a}\n")
        return out.getvalue()

    @staticmethod
    def get_default():
        return _load_default_policy()


_policy: Policy = None


def _load_default_policy():
    global _policy

    if not _policy:
        _policy = Policy.load(_default_policy_document())

    return _policy


def _default_policy_document() -> str:
    return os.getenv(
        "IAM_SUDO_POLICY",
        """
    allowed-role-names:
    - "*"
    allowed-principals:
    - "*" : "*"
    allowed-base-roles:
    - "arn:aws:iam::*:role/*"
    """,
    )
