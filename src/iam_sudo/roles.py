import sys
from copy import deepcopy
import boto3
import logging
import json
import datetime
from typing import List, Optional
from iam_sudo.principal import Principal


iam = boto3.client("iam")


class Roles(list):
    def __init__(self, roles: List["Role"] = []):
        super(Roles, self).__init__()
        self.extend(roles)

    @staticmethod
    def load_from_file(path: str) -> "Roles":
        with open(path, "r") as f:
            return Roles(list(map(lambda r: Role(r), json.load(f))))

    def filter_by_substring_of_name(self, role_name: str) -> "Roles":
        return Roles(list((filter(lambda r: role_name in r.name, self))))

    def filter_by_principal(self, principal: Principal) -> "Roles":
        return Roles(list(filter(lambda r: principal in r.principals, self)))


class Role(dict):
    def __init__(self, role: dict):
        super(Role, self).__init__()
        self.update(role)

    @property
    def name(self):
        return self["RoleName"]

    @property
    def arn(self):
        return self["Arn"]

    @property
    def principals(self) -> List[Principal]:
        result = []
        statement = self.get("AssumeRolePolicyDocument", {}).get("Statement", [])
        p = statement[0].get("Principal") if statement else None
        if not p:
            return []

        for typ, identifiers in p.items():
            for identifier in (
                identifiers if isinstance(identifiers, list) else [identifiers]
            ):
                result.append(Principal(typ, identifier))
        return result

    @property
    def attached_policies(self) -> list:
        result = []
        for response in iam.get_paginator("list_attached_role_policies").paginate(
            RoleName=self.name
        ):
            for policy in response["AttachedPolicies"]:
                result.append(policy["PolicyArn"])
        return result

    @property
    def inline_policies(self) -> dict:
        result = {}
        for response in iam.get_paginator("list_role_policies").paginate(
            RoleName=self.name
        ):
            for policy_name in response["PolicyNames"]:
                r = iam.get_role_policy(RoleName=self.name, PolicyName=policy_name)
                result[policy_name] = r["PolicyDocument"]

        return result

    @property
    def merged_inlined_policy(self) -> dict:
        result = {}
        for name, doc in self.inline_policies.items():
            if result:
                result["Statement"].extend(doc.get("Statement", []))
            else:
                result = deepcopy(doc)

        return result

    @staticmethod
    def get_all() -> Roles:
        result = []
        for response in iam.get_paginator("list_roles").paginate():
            result.extend(map(lambda r: Role(r), response["Roles"]))
        return Roles(result)

    @staticmethod
    def get_by_role_name(name: str) -> Optional["Role"]:
        try:
            r = iam.get_role(RoleName=name)
            return Role(r["Role"])
        except iam.exceptions.NoSuchEntity as e:
            return None
