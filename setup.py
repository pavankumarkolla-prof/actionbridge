from setuptools import setup, find_packages

setup(
    name="actionbridge",
    version="0.1.0",
    description="Signal-to-Action reference architecture for cost-to-serve reduction in manufacturing.",
    author="Pavan Kumar Kolla",
    url="https://github.com/pavankumarkolla-prof/actionbridge",
    packages=find_packages(exclude=["tests", "examples"]),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
)
