from setuptools import find_packages, setup

setup(
    name="runtool",
    version="0.1.0",
    author="Amazon",
    packages=find_packages("./runtool"),
    description="Gluonts run tool package",
    long_description=open("readme.md").read(),
    include_package_data=True,
    install_requires=[
        "boto3",
        "click",
        "botocore",
        "PyYAML",
        "beautifultable",
        "sagemaker",
        "pandas",
    ],
    entry_points={
        "console_scripts": ["runtool=runtool.__main__:cli"],
    },
)
