# NAME

   iam-sudo - get credentials to assume an IAM role

## SYNPOSIS
```
  iam-sudo [OPTIONS] [CMD]...
```

## OPTIONS
```
--role-name TEXT  of the role to get the credentials for  [required]
--principal TEXT  the role belongs to
--base-role TEXT  base role to assume
--profile TEXT    to save the credentials under
--remote          invoke lambda
```

## DESCRIPTION
iam-sudo will read the attached and inline policies of the specified `role-name` to create a session policy with.
The `base-role` is the role that will be assumed combined with the session policy.

`role-name` is a substring of the role to assume. This is to make it easier to assume a role that was created by
AWS CloudFormation. For instance, both `TaskRoles` and `my-stack-TaskRole` may resolve to
the role `my-stack-TaskRole-9AO01PCC7I0T`. If multiple matching roles are found, an error is returned.
You may also specify the `principal` to reduce the number of matching roles:
for instance `--principal Service:ecs-tasks.amazonaws.com`.

If a `profile` is specified, the credentials will be stored in `~/.aws/credentials` under the specified
name. if a command is specified, the command will be executed with the obtained credentials, through
the environment  variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN`.

The `remote` flag wil invoke the iam-sudo Lambda function to generate credentials. This remote option, is
required to really give use `sudo` like permissions which exceeds their own.  Without the `remote` flag,
the user will not be able to get more permissions, than granted to him/her.

## Sudo Policy
To limit the roles which can be assumed, a policy can be specified. The following snippet shows the default
sudo policy:

```yaml
allowed-role-names:
  - "*"
allowed-principals:
  - "*" : "*"
allowed-base-roles:
  - "arn:aws:iam::*:role/*"
```
It allows all role names, all principals and all base roles in the request. The following table
shows a short description of the fields.

| field | description |
| ----- | ------------|
| allowed-role-names| a list of glob patterns specifying allowed role names|
| allowed-principals| a list of glob patterns specifying principal type and identity |
| allowed-base-role | a list of glob patterns specifying allowed base roles|

The following policy, restricts requests to any AWS ECS task role and the base role to the IAmSudoRole.

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


```
aws cloudformation create-stack \
     --stack-name iam-sudo \
    --template-url  https://binxio-public-eu-central-1.s3.amazonaws.com/lambdas/iam-sudo-latest.yaml \
    --capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name iam-sudoi
```

Or launch via the [CloudFormation console](https://console.aws.amazon.com/cloudformation/home?#/stacks/new?stackName=iam-sudo&templateURL=https%3A%2F%2Fbinxio-public-eu-central-1.s3.amazonaws.com%2Flambdas%2Fiam-sudo-latest.yaml)

To allow users to use the remote function, they should be granted access to invoke the created Lambda function `iam-sudo`.

## ENVIRONMENT VARIABLES
The iam-sudo lambda function requires the following environment variables to be set:

| name | description|
|------|------------|
| IAM\_SUDO\_BASE\_ROLE | The role to assume over which the session policies are added, default `IAMSudoUser`|
| IAM\_SUDO\_POLICY | The policy which governs which roles can be assumed, default any |
