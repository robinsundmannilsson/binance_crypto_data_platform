"""A Python Pulumi program"""

import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
db_password = config.require_secret("db_password")


def get_image_digest(repo_name: str) -> str | None:
    """Return the digest of the :latest image in an ECR repo, or None if the
    repo or image does not exist yet. Lets the program deploy only the
    services whose images have been pushed — no deploy flags needed."""
    try:
        return aws.ecr.get_image(repository_name=repo_name, image_tag="latest").image_digest
    except Exception:
        return None


default_vpc = aws.ec2.get_vpc(default=True)
default_subnets = aws.ec2.get_subnets(filters=[{"name": "vpc-id", "values": [default_vpc.id]}])

rds_sg = aws.ec2.SecurityGroup(
    "rds-sg",
    vpc_id=default_vpc.id,
    ingress=[{"from_port": 5432, "to_port": 5432, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}],
    egress=[{"from_port": 0, "to_port": 0, "protocol": "-1", "cidr_blocks": ["0.0.0.0/0"]}],
)

subnet_group = aws.rds.SubnetGroup(
    "db-subnet-group",
    subnet_ids=default_subnets.ids,
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
    publicly_accessible=True,
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

dashboard_repo = aws.ecr.Repository(
    "crypto-data-platform-dashboard-repo",
    name="crypto-data-platform-dashboard-repo",
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

event_rule = aws.cloudwatch.EventRule(
    "ingest-schedule",
    schedule_expression="cron(0 0 * * ? *)",
)

ingest_digest = get_image_digest("crypto-data-platform-ingest-repo")
api_digest = get_image_digest("crypto-data-platform-api-repo")
dashboard_digest = get_image_digest("crypto-data-platform-dashboard-repo")

if ingest_digest:
    ingest_lambda = aws.lambda_.Function(
        "ingest-lambda",
        package_type="Image",
        image_uri=ingest_repo.repository_url.apply(lambda url: f"{url}@{ingest_digest}"),
        role=lambda_role.arn,
        timeout=300,
        memory_size=512,
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

if api_digest:
    api_lambda = aws.lambda_.Function(
        "api-lambda",
        package_type="Image",
        image_uri=api_repo.repository_url.apply(lambda url: f"{url}@{api_digest}"),
        role=lambda_role.arn,
        timeout=30,
        memory_size=512,
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

    pulumi.export("api_url", api_gateway.api_endpoint)

# The dashboard reads from the API, so it needs the API Gateway to exist
if api_digest and dashboard_digest:
    dashboard_sg = aws.ec2.SecurityGroup(
        "dashboard-sg",
        vpc_id=default_vpc.id,
        ingress=[{"from_port": 8501, "to_port": 8501, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}],
        egress=[{"from_port": 0, "to_port": 0, "protocol": "-1", "cidr_blocks": ["0.0.0.0/0"]}],
    )

    ecs_task_execution_role = aws.iam.Role(
        "ecs-task-execution-role",
        assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }""",
    )

    aws.iam.RolePolicyAttachment(
        "ecs-task-execution-policy",
        role=ecs_task_execution_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    )

    dashboard_log_group = aws.cloudwatch.LogGroup(
        "dashboard-logs",
        retention_in_days=7,
    )

    dashboard_cluster = aws.ecs.Cluster("dashboard-cluster")

    dashboard_task = aws.ecs.TaskDefinition(
        "dashboard-task",
        family="dashboard",
        cpu="256",
        memory="512",
        network_mode="awsvpc",
        requires_compatibilities=["FARGATE"],
        execution_role_arn=ecs_task_execution_role.arn,
        container_definitions=pulumi.Output.all(
            dashboard_repo.repository_url,
            api_gateway.api_endpoint,
            dashboard_log_group.name,
        ).apply(lambda args: json.dumps([{
            "name": "dashboard",
            "image": f"{args[0]}@{dashboard_digest}",
            "portMappings": [{"containerPort": 8501, "protocol": "tcp"}],
            "environment": [{"name": "API_BASE", "value": args[1]}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": args[2],
                    "awslogs-region": aws.get_region().name,
                    "awslogs-stream-prefix": "dashboard",
                },
            },
        }])),
    )

    dashboard_service = aws.ecs.Service(
        "dashboard-service",
        cluster=dashboard_cluster.arn,
        desired_count=1,
        launch_type="FARGATE",
        task_definition=dashboard_task.arn,
        network_configuration={
            "assign_public_ip": True,
            "subnets": default_subnets.ids,
            "security_groups": [dashboard_sg.id],
        },
    )

    pulumi.export("dashboard_cluster_name", dashboard_cluster.name)
    pulumi.export("dashboard_service_name", dashboard_service.name)
