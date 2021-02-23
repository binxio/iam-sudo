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
import datetime
import json
import logging
from typing import Optional
import botocore

import boto3

from iam_sudo.credentials import Credentials
from iam_sudo.principal import Principal
from iam_sudo.roles import Role
from iam_sudo.sudo_policy import Policy

sts = boto3.client("sts")


class AssumeRoleError(Exception):
    def __init__(self, e):
        super(AssumeRoleError, self).__init__(e)


def find_role(name: str, principal: Optional[Principal]) -> Role:
    roles = Role.get_all().filter_by_substring_of_name(name)
    if principal:
        roles = roles.filter_by_principal(principal)

    if len(roles) == 1:
        return roles[0]

    msg = (
        f"matching name {name} and principal" if principal else f"matching name {name}"
    )
    if roles:
        r = list(filter(lambda r: r.name == name, roles))
        if len(r) == 1:
            return r[0]

        raise AssumeRoleError(f"found multiple roles {msg}")
    else:
        raise AssumeRoleError(f"no roles {msg}")


def resolve_base_role(role_name: str) -> str:
    if role_name.startswith("arn:"):
        return role_name

    r = sts.get_caller_identity()
    return f"arn:aws:iam::{r['Account']}:role/{role_name}"


def convert_timestamp(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()


def real_assume_role(role_name: str):

    role_arn = resolve_base_role(role_name)
    name = role_arn.split("/")[-1]
    role = Role({"Arn": role_arn, "RoleName": name})

    try:
        result = sts.assume_role(
            RoleArn=role.arn,
            RoleSessionName=f"iam-sudo-{role.name}",
            DurationSeconds=3600,
        )
    except Exception as e:
        raise AssumeRoleError(e)

    return Credentials(result["Credentials"])


def simulate_assume_role(base_role: str, role_name: str, principal: str) -> Credentials:

    policy = Policy.get_default()

    base_role = resolve_base_role(base_role)
    if not policy.is_allowed_base_role(base_role):
        raise AssumeRoleError(f"Policy does not allow the base role {base_role}")

    if not policy.is_allowed_role_name(role_name):
        raise AssumeRoleError(f"Policy does not allow the role {role_name}")

    p = Principal.create_from_string(principal) if principal else None
    if p and not policy.is_allowed_principal(p):
        raise AssumeRoleError(f"Policy does not allow a role for principal {p}")

    role = find_role(role_name, p)

    if not policy.is_allowed_role(role):
        raise AssumeRoleError(f"Policy does not allow to assume the role {role.name}")

    kwargs = {
        "RoleArn": base_role,
        "RoleSessionName": f"iam-sudo-{role_name}",
        "DurationSeconds": 3600,
    }

    if role.attached_policies:
        kwargs["PolicyArns"] = [{"arn": arn} for arn in role.attached_policies]

    if role.inline_policies:
        kwargs["Policy"] = json.dumps(role.merged_inlined_policy)

    try:
        result = sts.assume_role(**kwargs)
    except Exception as e:
        raise AssumeRoleError(e)

    return Credentials(result["Credentials"])



def remote_assume_role(
    role_name: str, base_role: str, principal: str
) -> Credentials:

    request = {"role_name": role_name}
    if principal:
        request["principal"] = principal
    if base_role:
        request["base_role"] = base_role

    client = boto3.client("lambda")
    try:
        response = client.invoke(
            FunctionName="iam-sudo",
            InvocationType="RequestResponse",
            Payload=json.dumps(request).encode("utf-8"),
        )
    except botocore.exceptions.ClientError as e:
        raise AssumeRoleError(f"{e}")

    reply = {}
    try:
        reply = json.load(response["Payload"])
    except Exception as e:
        logging.debug("failed to load the json message from the response, %s", e)

    function_error = response.get("FunctionError")
    if function_error:
        error_message = reply.get(
            "errorMessage", "unknown error occurred while invoking lambda"
        )
        raise AssumeRoleError(f"{error_message}")

    return Credentials(reply)
