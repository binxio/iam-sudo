import json
from os import path
from iam_sudo.sudo_policy import Policy
from iam_sudo.roles import Roles
from iam_sudo.principal import Principal


def test_is_allowed_role_name():
    policy = Policy()
    policy.allowed_role_names = ["*"]
    assert policy.is_allowed_role_name("No")
    assert policy.is_allowed_role_name("Yes")
    assert policy.is_allowed_role_name("*")

    policy.allowed_role_names = ["N*"]
    assert policy.is_allowed_role_name("No")
    assert not policy.is_allowed_role_name("OhNo")
    assert not policy.is_allowed_role_name("Yes")
    assert not policy.is_allowed_role_name("*")

    policy.allowed_role_names = ["*N*"]
    assert policy.is_allowed_role_name("No")
    assert policy.is_allowed_role_name("OhNo")
    assert not policy.is_allowed_role_name("Yes")
    assert not policy.is_allowed_role_name("*")


def test_is_allowed_principal():
    policy = Policy()
    policy.allowed_principals = [Principal("*", "*")]
    assert policy.is_allowed_principal(Principal("Service", "codebuild.amazonaws.com"))
    assert policy.is_allowed_principal(
        Principal("AWS", "arn:aws:iam::123456789013:root")
    )

    policy.allowed_principals = [Principal("Service", "*")]
    assert policy.is_allowed_principal(Principal("Service", "codebuild.amazonaws.com"))
    assert not policy.is_allowed_principal(
        Principal("AWS", "arn:aws:iam::123456789013:root")
    )

    policy.allowed_principals = [Principal("*", "arn:aws:iam::123456789013:root")]
    assert not policy.is_allowed_principal(
        Principal("Service", "codebuild.amazonaws.com")
    )
    assert policy.is_allowed_principal(
        Principal("AWS", "arn:aws:iam::123456789013:root")
    )

    policy.allowed_principals = [Principal("*", "arn:aws:iam::12*:*")]
    assert not policy.is_allowed_principal(
        Principal("Service", "codebuild.amazonaws.com")
    )
    assert policy.is_allowed_principal(
        Principal("AWS", "arn:aws:iam::123456789013:root")
    )


def test_is_allowed_base_role():
    policy = Policy()
    policy.allowed_base_roles = ["*"]
    assert policy.is_allowed_base_role("arn:aws:iam::12344534545:role/No")
    assert not policy.is_allowed_base_role("No")

    policy.allowed_base_roles = ["arn:aws:iam::*:role/N*"]
    assert not policy.is_allowed_base_role("arn:aws:iam::12344534545:role/Yes")
    assert policy.is_allowed_base_role("arn:aws:iam::12344534545:role/No")


def test_load_policy():
    p = """
    allowed-role-names:
      - "*"
    allowed-principals:
      - Service: codebuild.amazonaws.com
    allowed-base-roles:
      - arn:aws:iam::444093529715:role/aws-*  
    """
    policy = Policy.load(p)

    roles = Roles.load_from_file(path.join(path.dirname(__file__), "roles.json"))
    allowed_roles = policy.allowed_roles(roles)

    assert len(allowed_roles) == 1
    assert allowed_roles[0].name == "aws-account-destroyer"

    p = """
    allowed-role-names:
      - "*account-destroyer*"
    allowed-principals:
      - Service: "lambda*"
      - Service: "events*"
    allowed-base-roles:
      - arn:aws:iam::444093529715:role/aws-*  
    """
    policy = Policy.load(p)

    roles = Roles.load_from_file(path.join(path.dirname(__file__), "roles.json"))
    allowed_roles = policy.allowed_roles(roles)

    assert len(allowed_roles) == 2
    assert allowed_roles[0].name == "aws-account-destroyer-build-trigger"
    assert allowed_roles[1].name == "aws-account-destroyer-event-trigger"
