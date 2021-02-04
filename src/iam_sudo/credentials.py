#
# Copyright 2019 - binx.io B.V.
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
import os
import subprocess
import sys
from typing import List
import logging
import configparser
from os import chmod, path


class Credentials(object):
    def __init__(self, credentials: dict):
        assert "AccessKeyId" in credentials
        assert "SecretAccessKey" in credentials
        assert "SessionToken" in credentials
        assert "Expiration" in credentials
        self.credentials = credentials

    def to_shell(self) -> str:
        return f"""
export AWS_ACCESS_KEY_ID="{self.aws_access_key_id}";
export AWS_SECRET_ACCESS_KEY="{self.aws_secret_access_key}";
export AWS_SESSION_TOKEN="{self.aws_session_token}";
    """

    def to_aws_config(self) -> str:
        return f"""
aws configure set aws_access_key_id "{self.aws_access_key_id}"
aws configure set aws_secret_access_key "{self.aws_secret_access_key}"
aws configure set aws_session_token "{self.aws_session_token}"
    """

    def to_json(self):
        return json.dumps(self.credentials, default=_convert_timestamp, indent=2)

    @property
    def aws_access_key_id(self):
        return self.credentials["AccessKeyId"]

    @property
    def aws_secret_access_key(self):
        return self.credentials["SecretAccessKey"]

    @property
    def aws_session_token(self):
        return self.credentials["SessionToken"]

    @property
    def expiration(self):
        return self.credentials["Expiration"]

    def __repr__(self):
        return self.format("json")

    def format(self, style: str = "json") -> str:
        if style == "shell":
            return self.to_shell()
        if style == "aws":
            return self.to_aws_config()
        return self.to_json()

    def new_env(self) -> List[str]:
        env = os.environ
        env["AWS_ACCESS_KEY_ID"] = self.aws_access_key_id
        env["AWS_SECRET_ACCESS_KEY"] = self.aws_secret_access_key
        env["AWS_SESSION_TOKEN"] = self.aws_session_token
        return env

    def run(self, cmd: List[str]):

        r = subprocess.run(
            args=cmd,
            env=self.new_env(),
            text=False,
            shell=False,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        exit(r.returncode)

    def write_aws_config(self, profile: str):
        filename = path.expanduser(path.expandvars("~/.aws/credentials"))
        config = configparser.ConfigParser()
        config.read(filename)
        if not config.has_section(profile):
            config.add_section(profile)
        config.set(profile, "aws_access_key_id", self.aws_access_key_id)
        config.set(profile, "aws_secret_access_key", self.aws_secret_access_key)
        config.set(profile, "aws_session_token", self.aws_session_token)
        config.set(profile, "expiration", f"{self.expiration}")
        with open(filename, "w") as f:
            config.write(f)
        chmod(filename, 0o600)
        logging.info(f"credentials saved under AWS profile {profile}.")


def _convert_timestamp(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
