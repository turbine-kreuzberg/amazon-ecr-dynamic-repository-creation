import logging
import os
import sys
import boto3
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


lifecycle_policy = {
    "rules": [
        {
            "rulePriority": 1,
            "description": "Retain most recent 30 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 30
            },
            "action": {
                "type": "retain"
            }
        },
        {
            "rulePriority": 2,
            "description": "Delete images older than 30 days",
            "selection": {
                "tagStatus": "any",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 30
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}

def run(event, context):
    account_id = event["account"]
    repository = event["detail"]["requestParameters"]["repositoryName"]

    filter_by_prefix  = os.environ["FILTER_BY_PREFIX"]

    if not repository.startswith(filter_by_prefix):
        logger.info("the repository %s is out of scope prefix (%s)", repository, filter_by_prefix)
        sys.exit(0)

    client = boto3.client("ecr")

    try:
        repositories = client.describe_repositories(
            registryId=account_id, repositoryNames=[repository]
        )["repositories"]
    except:
        logger.info("failed to lookup repository %s, probably missing - creating the repository now...", repository)
        repositories = []

    if not repositories:
        try:
            scan_on_push = bool(os.environ["REPO_SCAN_ON_PUSH"])
            mutability   = os.environ["IMAGE_TAG_MUTABILITY"]

            if os.environ["REPO_TAGS"]:
                 tags = [{"Key": k, "Value": v} for (k, v) in json.loads(os.environ["REPO_TAGS"]).items()]
        except Exception as e:
            logger.error("env variable malformed: %s", e)
            sys.exit(1)

        try:
            client.create_repository(
                registryId=account_id,
                repositoryName=repository,
                imageTagMutability=mutability,
                imageScanningConfiguration={"scanOnPush": scan_on_push},
                encryptionConfiguration={"encryptionType": "KMS"},
                tags=tags,
            )
            logger.info("created %s repository", repository)

            client.put_lifecycle_policy(
                repositoryName=repository,
                lifecyclePolicyText=json.dumps(lifecycle_policy)
            )
            logger.info("created lifecycle policy for %s", repository)
        except Exception as e:
            logger.error("failed to create repository %s: %s", repository, e)
            sys.exit(1)
