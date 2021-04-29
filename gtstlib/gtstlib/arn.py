from typing import NamedTuple

from toolz import first, second


class Arn(NamedTuple):
    # arn:partition:service:region:account-id:<resource>`
    # where resource is one of
    # [resource-id, resource-type/resource-id, resource-type:resource-id]
    service: str
    region: str
    account: str
    resource: str

    @staticmethod
    def parse(arn: str) -> "Arn":
        # we can ignore the leading `arn:aws`
        elements = arn.split(":", 5)[2:]
        kwargs = dict(
            zip(["service", "region", "account", "resource"], elements)
        )

        return Arn(**kwargs)

    @classmethod
    def __get_validators__(cls):
        # For pydantic
        yield cls.parse

    def resource_split(self):
        """Return a pair of (resource_type, resource_id).

        For example, an s3-path would return:

            <bucket>, <key>

        However, in cases where the resource can't be split, it returns the
        resource twice.

        Given just a s3-bucket-arn, we get:

            <bucket>, <bucket>
        """
        for sep in ":", "/":
            if sep in self.resource:
                return self.resource.split(sep, 1)

        return self.resource, self.resource

    @property
    def resource_type(self):
        return first(self.resource_split())

    @property
    def resource_id(self):
        return second(self.resource_split())

    def __str__(self):
        return (
            "arn:aws:"
            f"{self.service}:{self.region}:{self.account}:{self.resource}"
        )
