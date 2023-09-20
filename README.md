# NAME

   iam-sudo - get credentials of a real or simulated IAM role

## Usage

```
Usage: iam-sudo assume [OPTIONS] [CMD]...

Options:
--role-name NAME   to assume  [required]
--profile PROFILE  to save the credentials under

```

```
Usage: iam-sudo simulate [OPTIONS] [CMD]...

Options:
  --role-name NAME       to simulate  [required]
  --principal PRINCIPAL  of the simulated role
  --base-role NAME       to assume to simulate the role
  --remote / --local     invoke lambda, default --remote
  --profile PROFILE      to save the credentials under
```

## DESCRIPTION

iam-sudo supports the `assume` and the `simulate` commands.

### assume command
this command will assume the specified role and return the credentials.

If a `profile` is specified, the credentials will be stored in `~/.aws/credentials`.

If a command is specified, it will be executed with the obtained credentials. This is done
by setting the environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN`.


## simulate command
iam-sudo simulate will read the attached policies and inline policies of the specified `role-name`.
These policies will be used to create the session policy. The `base-role` is the
role that will be assumed combined with the session policy, to mimic the specified role.

`role-name` is a substring of the role to assume. This is to make it easier to assume a
role that was created by AWS CloudFormation. For instance, both `TaskRoles`
and `my-stack-TaskRole` may resolve to the role `my-stack-TaskRole-9AO01PCC7I0T`.

If multiple matching roles are found, an error is returned. You may also specify
the `principal` to reduce the number of matching roles: for
instance `--principal Service:ecs-tasks.amazonaws.com`.

If a `profile` is specified, the credentials will be stored in `~/.aws/credentials`.

If a command is specified, it will be executed with the obtained credentials. This is done
by setting the environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN`.

The `remote` flag wil invoke the iam-sudo Lambda function to generate credentials. This
remote option, is required to really give users sudo-like permissions which exceeds
their own. Without the `remote` flag, the user will not be able to get more
permissions, than granted to him/her.

### Sudo simulated Policy
To limit the roles which can be simulated, a policy can be specified. The following
snippet shows the default sudo policy:

```yaml
allowed-role-names:
  - "*"
allowed-principals:
  - "*" : "*"
allowed-base-roles:
  - "arn:aws:iam::*:role/*"
```
The following table shows a short description of the fields.

| field | description |
| ----- | ------------|
| allowed-role-names| a list of glob patterns specifying allowed role names|
| allowed-principals| a list of glob patterns specifying principal type and identity |
| allowed-base-role | a list of glob patterns specifying allowed base roles|

The default client policy is to allow all role names, all principals and all base
roles to be specified.

The following policy, restricts requests to any AWS ECS task role and the base
role to the IAmSudoUser.

```yaml
allowed-role-names:
  - "*"
allowed-principals:
  - "Service" : "ecs-tasks.amazonaws.com"
allowed-base-roles:
  - "arn:aws:iam::123456789012:role/IAMSudoUser"
```

## installation
The installation comes in two parts: the client and the server.

To install the client, type:

```sh
pip install iam-sudo
```

To install the server, type:

```
aws cloudformation create-stack \
     --stack-name iam-sudo \
    --template-url  https://binxio-public-eu-central-1.s3.amazonaws.com/lambdas/iam-sudo-0.3.0.yaml \
    --capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name iam-sudo
```

Alternatively, you can create the stack via
the [AWS console](https://console.aws.amazon.com/cloudformation/home?#/stacks/new?stackName=iam-sudo&templateURL=https%3A%2F%2Fbinxio-public-eu-central-1.s3.amazonaws.com%2Flambdas%2Fiam-sudo-0.3.0.yaml).

To allow users to use the remote function, they should be granted permission to
invoke the created Lambda function `iam-sudo`.

## ENVIRONMENT VARIABLES
The iam-sudo simulate allows following environment variables to be set:

| name | description|
|------|------------|
| IAM\_SUDO\_BASE\_ROLE | The role to assume over which the session policies are added, default `IAMSudoUser`|
| IAM\_SUDO\_POLICY | The policy which governs which roles can be assumed, default any |

The lambda function requires you to set both.

Read the blog [How to assume an ECS task role in AWS, the official and the fake way](https://binx.io/blog/2021/02/27/how-to-simulate-an-ecs-task-role-in-aws/).
