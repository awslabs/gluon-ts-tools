from unittest.mock import MagicMock

from sagetest import SageTest
from sagetest.jobs import Job, Jobs
from sagetest.search import Filter


def search_sideffect(filters):
    job = Job(metrics={}, training_time=100, hyperparameters={}, tags={})
    return Jobs([job] * len(filters.names))


sagetest = SageTest(None)  # None due to mocking
sagetest.search = MagicMock()
sagetest.search.side_effect = search_sideffect


FILTER = lambda num_names: Filter(
    names=[f"test_{i}" for i in range(num_names)]
)


@sagetest.fixture()
def my_jobs():
    return FILTER(1)


def test_fixture(my_jobs):
    assert isinstance(my_jobs, Jobs)
    sagetest.search.assert_any_call(FILTER(1))


@sagetest.parametrize("jobs", [FILTER(2), FILTER(2)])
def test_parametrize(jobs):
    assert isinstance(jobs, Jobs)
    assert len(jobs) == 2
    sagetest.search.assert_any_call(FILTER(2))
    sagetest.search.assert_any_call(FILTER(2))


@sagetest.parametrize(
    "foo,jobs,len_jobs,more_jobs,bar",
    [
        ("hi", FILTER(3), 3, FILTER(4), [1, 2, 3]),
        ("hi", FILTER(5), 5, FILTER(6), [1, 2, 3]),
    ],
)
def test_parametrize_complicated_with_fixture(
    foo, jobs, len_jobs, more_jobs, bar, my_jobs
):
    """
    Test to ensure that ordering of parametrized values are maintained and
    that other fixtures can be used with sagetest.parametrize.
    """
    assert foo == "hi"
    assert bar == [1, 2, 3]

    assert isinstance(len_jobs, int)

    assert isinstance(jobs, Jobs)
    assert isinstance(more_jobs, Jobs)
    assert isinstance(my_jobs, Jobs)

    assert len(jobs) == len_jobs
    assert len(more_jobs) == len_jobs + 1
    assert len(my_jobs) == 1

    sagetest.search.assert_any_call(FILTER(3))
    sagetest.search.assert_any_call(FILTER(4))
    sagetest.search.assert_any_call(FILTER(5))
    sagetest.search.assert_any_call(FILTER(6))
