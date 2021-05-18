#!/bin/sh
pytest ./test_cli_example --sagetest-fixtures={"my_fixture": {"names": ["some-job"]}} 
