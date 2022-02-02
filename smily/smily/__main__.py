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

import sys


def main():
    try:
        import click
    except ImportError:
        print(
            "`click` not installed. Try `pip installl smily[cli]` to ensure all "
            "dependencies are installed."
        )
        sys.exit(1)

    from .cli import main

    main()


if __name__ == "__main__":
    main()
