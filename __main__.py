"""An AWS Python Pulumi program"""
import pulumi
from pulumi_aws import lambda_, iam, sns, cloudwatch
import pulumi_aws_apigateway as apigateway
import json
import os

# Allow lambda assume role
lambda_role = iam.Role(
    resource_name="lambda-sentiment-analysis-reconciliation", 
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com",
                    },
                    "Effect": "Allow",
                    "Sid": "allowLambdaAssume",
                }
            ]
        }
    ))

# Create SNS Topic and add email target
sns_topic = sns.Topic("sentiment-analysis-reconciliation")
sns_email_target = sns.TopicSubscription(
    resource_name="sentiment-analysis-reconciliation-email",
    endpoint=os.environ['SNS_EMAIL'],
    protocol="email",
    topic=sns_topic.arn
)

# Create function
lambda_function = lambda_.Function(
    resource_name="sentiment-analysis-reconciliation",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./function")
    }),
    environment={
        "variables": {
            "topic_target_arn": sns_topic.arn
        }
    },
    runtime="python3.8",
    role=lambda_role.arn,
    handler="index.lambda_handler"
)

# Make log group for Lambda function
log_group = cloudwatch.LogGroup(
    resource_name="sentiment-analysis-reconciliation-log-group",
    name=lambda_function.name.apply(
        lambda function_name: "/aws/lambda/" + function_name
    ),
    retention_in_days=7,
    opts=pulumi.ResourceOptions(depends_on=[
        lambda_function
    ])
)

# Create SNS, Comprehend, and Log Group policy
lambda_iam_policy = iam.Policy(
    resource_name="sentiment-analysis-reconciliation-policy",
    opts=pulumi.ResourceOptions(depends_on=[
        log_group,
        sns_topic
    ]),
    policy=pulumi.Output.all(sns_arn=sns_topic.arn, log_group_arn=log_group.arn).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "sns:Publish"
                    ],
                    "Effect": "Allow",
                    "Resource": args['sns_arn']
                },
                {
                    "Action": [
                        "comprehend:DetectSentiment"
                    ],
                    "Effect": "Allow",
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        args['log_group_arn'] + ':*'
                    ]
                }
            ]
        })
    )
)

# Attach policy to role
role_policy_attach = iam.RolePolicyAttachment(
    resource_name="sentiment-analysis-reconciliation",
    role=lambda_role.name,
    policy_arn=lambda_iam_policy.arn
)

# API Gateway
api_gateway = apigateway.RestAPI('api', routes=[
    apigateway.RouteArgs(path="/sentiment", method="POST", event_handler=lambda_function),
])

pulumi.export('api_gateway', api_gateway.url)