"""A Python Pulumi program"""

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
db_password = config.require_secret("db_password")

vpc = aws.ec2.Vpc(
    "crypto-data-platform-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

subnet_a = aws.ec2.Subnet(
    "crypto-data-platform-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="<AWS_REGION>a",
)

subnet_b = aws.ec2.Subnet(
    "crypto-data-platform-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="<AWS_REGION>b",
)

subnet_group = aws.rds.SubnetGroup(
    "crypto-data-platform-subnet-group",
    subnet_ids=[subnet_a.id, subnet_b.id],
)

rds_sg = aws.ec2.SecurityGroup(
    "crypto-data-platform-rds-sg",
    vpc_id=vpc.id,
    description="Allow access to RDS",
    ingress=[{
        "from_port": 5432,
        "to_port": 5432,
        "protocol": "tcp",
        "cidr_blocks": ["10.0.0.0/16"],
    }],
    egress=[{
        "from_port": 0,
        "to_port": 0,
        "protocol": "-1",
        "cidr_blocks": ["0.0.0.0/0"],
    }],
)

db = aws.rds.Instance(
    "crypto-data-platform-db",
    engine="postgres",
    engine_version="18.4",
    instance_class="db.t4g.micro",
    allocated_storage=20,
    db_name="binance_crypto_data",
    username="dbadmin",
    password=db_password,
    db_subnet_group_name=subnet_group.name,
    vpc_security_group_ids=[rds_sg.id],
    skip_final_snapshot=True,
    publicly_accessible=False,
)

ingest_repo = aws.ecr.Repository(
    "crypto-data-platform-ingest-repo",
    name="crypto-data-platform-ingest-repo",
    force_delete=True,
)

api_repo = aws.ecr.Repository(
    "crypto-data-platform-api-repo",
    name="crypto-data-platform-api-repo",
    force_delete=True,
)

lambda_role = aws.iam.Role(
    "lambda-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }""",
)

aws.iam.RolePolicyAttachment(
    "lambda-basic-execution",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

aws.iam.RolePolicyAttachment(
    "lambda-vpc-execution",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
)

ingest_lambda = aws.lambda_.Function(
    "ingest-lambda",
    package_type="Image",
    image_uri=ingest_repo.repository_url.apply(lambda url: f"{url}:latest"),
    role=lambda_role.arn,
    timeout=300,
    memory_size=512,
    vpc_config={
        "subnet_ids": [subnet_a.id, subnet_b.id],
        "security_group_ids": [rds_sg.id],
    },
    environment={
        "variables": {
            "DB_HOST": db.address,
            "DB_NAME": "binance_crypto_data",
            "DB_USER": "dbadmin",
            "DB_PASSWORD": db_password,
            "DB_PORT": "5432",
            "BASE_URL": "https://api.binance.com/api/v3/klines",
            "SYMBOLS": "BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,LINKUSDT,ADAUSDT",
            "INTERVAL": "1d",
            "START_DATE": "2000-01-01",
        }
    },
)

api_lambda = aws.lambda_.Function(
    "api-lambda",
    package_type="Image",
    image_uri=api_repo.repository_url.apply(lambda url: f"{url}:latest"),
    role=lambda_role.arn,
    timeout=30,
    memory_size=512,
    vpc_config={
        "subnet_ids": [subnet_a.id, subnet_b.id],
        "security_group_ids": [rds_sg.id],
    },
    environment={
        "variables": {
            "DB_HOST": db.address,
            "DB_NAME": "binance_crypto_data",
            "DB_USER": "dbadmin",
            "DB_PASSWORD": db_password,
            "DB_PORT": "5432",
        }
    },
)

api_gateway = aws.apigatewayv2.Api(
    "crypto-data-platform-api-gateway",
    protocol_type="HTTP",
    target=api_lambda.arn,
)

aws.lambda_.Permission(
    "api-gateway-permission",
    action="lambda:InvokeFunction",
    function=api_lambda.name,
    principal="apigateway.amazonaws.com",
    source_arn=api_gateway.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)

event_rule = aws.cloudwatch.EventRule(
    "ingest-schedule",
    schedule_expression="cron(0 0 * * ? *)",
)

aws.cloudwatch.EventTarget(
    "ingest-target",
    rule=event_rule.name,
    arn=ingest_lambda.arn,
)

aws.lambda_.Permission(
    "eventbridge-permission",
    action="lambda:InvokeFunction",
    function=ingest_lambda.name,
    principal="events.amazonaws.com",
    source_arn=event_rule.arn,
)
