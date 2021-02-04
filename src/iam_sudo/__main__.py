import os
import logging
import click
from iam_sudo.sudo import remote_assume_role, assume_role, AssumeRoleError


@click.command(help="get credentials to assume an IAM role")
@click.pass_context
@click.option(
    "--role-name", required=True, help="of the role to get the credentials for"
)
@click.option("--principal", required=False, help="the role belongs to")
@click.option("--base-role", required=False, help="base role to assume")
@click.option("--profile", required=False, help="to save the credentials under")
@click.option("--remote", required=False, is_flag=True, help="invoke lambda")
@click.option("--verbose", required=False, is_flag=True, help="log output")
@click.argument("CMD", nargs=-1)
def main(ctx, role_name, principal, base_role, profile, remote, cmd, verbose):
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=os.getenv("LOG_LEVEL", "DEBUG" if verbose else "INFO"),
    )
    try:
        if not remote and not cmd:
            raise click.UsageError("specify --profile, a command or both")
        if remote:
            credentials = remote_assume_role(base_role, role_name, principal)
        else:
            if not base_role:
                base_role = "IAMSudoUser"
            credentials = assume_role(base_role, role_name, principal)

        if profile:
            credentials.write_aws_config(profile)
        if cmd:
            credentials.run(cmd)

    except AssumeRoleError as e:
        logging.error(f"{e}")
        exit(1)


if __name__ == "__main__":
    main()
