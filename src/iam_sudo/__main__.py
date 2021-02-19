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

from iam_sudo.sudo import AssumeRoleError, assume_role, remote_assume_role


@click.command(help="get credentials to assume an IAM role")
@click.option(
    "--role-name", required=True, help="of the role to get the credentials for"
)
@click.option("--profile", required=False, help="to save the credentials under")
@click.option(
    "--actual/--simulated",
    required=False,
    default=True,
    help="actual or simulated role",
)
@click.option("--principal", required=False, help="of the simulated role")
@click.option("--base-role", required=False, help="of a simulated role")
@click.option(
    "--remote/--local",
    default=True,
    required=False,
    is_flag=True,
    help="invoke lambda, default --remote",
)
@click.option("--verbose", required=False, is_flag=True, help="log output")
@click.argument("CMD", nargs=-1)
def main(role_name, profile, actual, principal, base_role, remote, cmd, verbose):
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=os.getenv("LOG_LEVEL", "DEBUG" if verbose else "INFO"),
    )
    try:
        if actual and base_role:
            raise click.UsageError(
                "--base-role is only applicable for a --simulated assume role"
            )
        if actual and principal:
            raise click.UsageError(
                "--principal is not applicable for a --simulated assume role"
            )

        if not profile and not cmd:
            raise click.UsageError("specify --profile, a command or both")

        if remote:
            credentials = remote_assume_role(role_name, base_role, principal, actual)
        else:
            if not actual and not base_role:
                base_role = os.getenv("IAM_SUDO_BASE_ROLE", "IAMSudoRole")
            credentials = assume_role(base_role, role_name, principal, actual)

        if profile:
            credentials.write_aws_config(profile)
        if cmd:
            r = credentials.run(cmd)
            exit(r.returncode)

    except AssumeRoleError as e:
        logging.error(f"{e}")
        exit(1)


if __name__ == "__main__":
    main()
