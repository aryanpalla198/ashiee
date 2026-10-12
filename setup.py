from setuptools import setup, find_packages

setup(
    name="ashiee",
    version="1.0.0",
    description="Autonomous AI-First Pair Programmer & Agentic Runtime",
    author="Ashiee Engineering Team",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "prompt_toolkit>=3.0.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "websockets>=12.0",
    ],
    entry_points={
        "console_scripts": [
            "ashiee=ashiee.cli.main:cli",
        ],
    },
)
