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

db = aws.rds.Instance("crypto-data-platform-db",
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