#!/bin/sh
pytest ./test_cli_example --sagetest-filters='{"my_jobs": {"names": ["some-job"]}}'
