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
from typing import Any, Dict, Iterable, List, Tuple, Union

import boto3
import pytest

from .jobs import Jobs
from .search import Filter, query


class SageTest:
    def __init__(self, _locals, session=boto3.Session()) -> None:
        self.locals = _locals
        self.session = session
        self.setup_sagetest_fixture()
        self.setup_commandline_fixtures()

    def setup_sagetest_fixture(self):
        """Make `self` available as pytest fixture `sagetest_instance`."""

        def sagetest_instance_fixture():
            yield self

        self.locals["sagetest_instance"] = pytest.fixture(
            name="sagetest_instance",
            fixture_function=sagetest_instance_fixture,
            scope="session",
            autouse=True,
        )

    def setup_commandline_fixtures(self):
        """Setup fixture from CLI arguments."""

        def fixture(pytestconfig) -> Dict[str, Jobs]:
            """Query SageMaker using args passed from --sagetest-fixtures."""
            filters = json.loads(pytestconfig.getoption("--sagetest-fixtures"))
            yield {
                fixture_name: self.search(Filter(**filterkwargs))
                for fixture_name, filterkwargs in filters.items()
            }

        self.locals["cli_fixtures"] = pytest.fixture(
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

    def fixture(
        self,
        fixture_name: str,
        filters: Union[List[Filter], Filter],
        scope: str = "session",
    ) -> List[Jobs]:
        """Create a pytest fixture where filters are transformed to `sagetest.Jobs`."""

        def fixture_function():
            yield self.search(filters)

        self.locals[fixture_name] = pytest.fixture(
            name=fixture_name, fixture_function=fixture_function, scope=scope
        )

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
