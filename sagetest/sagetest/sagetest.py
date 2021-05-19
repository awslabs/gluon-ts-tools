# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import json
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union
from _pytest.fixtures import FixtureLookupError

import boto3
import pytest

from .jobs import Jobs
from .search import Filter, query


class SageTest:
    def __init__(self, session=boto3.Session()) -> None:
        self.session = session

    def init_fixture(self, name="sagetest_instance"):
        def func():
            yield self

        return pytest.fixture(
            scope="session",
            autouse=True,
            name=name,
            fixture_function=func,
        )

    def init_cli(self, name="cli_fixtures"):
        """Setup fixture from CLI arguments."""

        def fixture(pytestconfig, request) -> Dict[str, Jobs]:
            """Query SageMaker using args passed from --sagetest-fixtures."""

            try:
                yield request.getfixturevalue(name)  # reuse if fixture exists
            except FixtureLookupError:
                filters = json.loads(
                    pytestconfig.getoption("--sagetest-fixtures")
                )
                yield {
                    fixture_name: self.search(Filter(**filterkwargs))
                    for fixture_name, filterkwargs in filters.items()
                }

        return pytest.fixture(
            name="cli_fixtures",
            fixture_function=fixture,
            scope="session",
            autouse=True,
        )

    def search(
        self, filters: Union[List[Filter], Filter]
    ) -> Union[List[Jobs], Jobs]:
        """Query sagemaker with each filter."""
        if isinstance(filters, Filter):
            return query(filters, self.session)
        return [query(_filter, self.session) for _filter in filters]

    def fixture(self, *args, **kwargs) -> Callable:
        """Create a pytest fixture where filters are transformed to `sagetest.Jobs`."""

        def decorator(func):
            @pytest.fixture(name=func.__name__, *args, **kwargs)
            def wrapper():
                yield self.search(func())

            return wrapper

        return decorator

    def parametrize(
        self,
        argnames: Iterable[str],
        argvalues: Iterable[Tuple[Filter, Any]],
    ):
        """
        Create a `pytest.parametrize` decorator populated with `Jobs`.

        Any `Filter` objects in the `argvalues` are used to query SageMaker
        for training jobs. The results will be passed to `pytest.parametrize`
        as `sagetest.Jobs` objects inplace of the filters used.
        """

        def update_parameters(
            parameters: Union[Tuple[Filter, ...], Filter, Any]
        ) -> Union[Tuple[Jobs, ...], Jobs, Any]:
            if isinstance(parameters, Filter):
                return self.search(parameters)

            if isinstance(parameters, Tuple):
                updated_params = tuple(
                    map(
                        lambda param: self.search(param)
                        if isinstance(param, Filter)
                        else param,
                        parameters,
                    )
                )
                return updated_params
            return parameters

        return pytest.mark.parametrize(
            argnames=argnames,
            argvalues=list(map(update_parameters, argvalues)),
        )
