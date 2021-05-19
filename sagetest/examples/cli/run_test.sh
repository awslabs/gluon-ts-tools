#!/bin/sh
pytest ./test_cli_example --sagetest-fixtures='{"my_jobs": {"names": ["some-job"]}}'
