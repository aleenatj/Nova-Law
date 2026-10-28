from enum import Enum


class LambdaFunctionName(str, Enum):
    """Lambda function name."""

    NOVA_LAW_API = "nova-law-api"