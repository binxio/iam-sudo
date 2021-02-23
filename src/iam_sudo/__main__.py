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
import logging
import os

import click
from collections import namedtuple

from iam_sudo.sudo import AssumeRoleError, simulate_assume_role, real_assume_role, remote_assume_role
from iam_sudo.principal import Principal



Setting = namedtuple("Setting", ["profile", "verbose"])

@click.group(help="get credentials of a real or simulated IAM role")
@click.option("--verbose", required=False, is_flag=True, help="log output")
def cli(verbose):
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=os.getenv("LOG_LEVEL", "DEBUG" if verbose else "INFO"),
    )

@cli.command("assume", help="the IAM role")
@click.option(
    "--role-name", required=True, help="to assume", metavar="NAME"
)
@click.option("--profile", required=False, help="to save the credentials under", metavar="PROFILE")
@click.argument("CMD", nargs=-1)
def assume(role_name, profile, cmd):
    try:
        if not profile and not cmd:
            raise click.UsageError("specify --profile, a command or both")

        credentials = real_assume_role(role_name)
        if profile:
            credentials.write_aws_config(profile)
        if cmd:
            r = credentials.run(cmd)
            exit(r.returncode)

    except AssumeRoleError as e:
        logging.error(f"{e}")
        exit(1)





@cli.command("simulate", help="an IAM role")
@click.option(
    "--role-name", required=True, help="to simulate", metavar="NAME"
)
@click.option("--principal", required=False, help="of the simulated role", metavar="PRINCIPAL", callback=Principal.click_option)
@click.option("--base-role", required=False, help="to assume to simulate the role", metavar="NAME")
@click.option(
    "--remote/--local",
    default=True,
    required=False,
    is_flag=True,
    help="invoke lambda, default --remote",
)
@click.option("--profile", required=False, help="to save the credentials under", metavar="PROFILE")
@click.argument("CMD", nargs=-1)
def simulate(role_name, profile, principal, base_role, remote, cmd):
    principal = str(principal) if principal else None
    try:
        if not profile and not cmd:
            raise click.UsageError("specify --profile, a command or both")

        if remote:
            credentials = remote_assume_role(role_name, base_role, principal)
        else:
            if not base_role:
                base_role = os.getenv("IAM_SUDO_BASE_ROLE", "IAMSudoRole")
            credentials = simulate_assume_role(base_role, role_name, principal)

        if profile:
            credentials.write_aws_config(profile)
        if cmd:
            r = credentials.run(cmd)
            exit(r.returncode)

    except AssumeRoleError as e:
        logging.error(f"{e}")
        exit(1)


if __name__ == "__main__":
    cli()
