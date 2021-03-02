from setuptools import find_packages, setup

setup(
    name="runtool",
    version="0.1.0",
    author="Amazon",
    packages=find_packages("./runtool"),
    description="Gluonts run tool package",
    include_package_data=True,
    install_requires=["PyYAML", "pydantic", "toolz"],
    entry_points={},
)
