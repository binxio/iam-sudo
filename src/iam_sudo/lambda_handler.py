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
import json
import logging
import os

import jsonschema

from iam_sudo.sudo import simulate_assume_role
from iam_sudo.sudo_policy import Policy

schema = {
    "type": "object",
    "required": ["role_name"],
    "properties": {
        "role_name": {"type": "string"},
        "principal": {"type": "string", "pattern": "[^:]+:[^:]+"},
        "base_role": {"type": "string"},
    },
}


def is_valid_request(request) -> bool:
    try:
        jsonschema.validate(request, schema)
        return True
    except jsonschema.ValidationError as e:
        logging.error("invalid request received: %s" % str(e.context))
        return False


_policy = None


def handler(request, context):
    if not os.getenv("IAM_SUDO_POLICY"):
        raise Exception("an explicit sudo policy is required")

    if not os.getenv("IAM_SUDO_BASE_ROLE"):
        raise Exception("an explicit sudo base role is required")

    global _policy
    if not _policy:
        _policy = Policy.get_default()
        logging.info("%s", _policy)

    if is_valid_request(request):
        credentials = simulate_assume_role(
            base_role=request.get("base_role", os.getenv("IAM_SUDO_BASE_ROLE")),
            principal=request.get("principal"),
            role_name=request["role_name"],
        )

        return json.loads(credentials.to_json())

    else:
        raise Exception("invalid request received.")
