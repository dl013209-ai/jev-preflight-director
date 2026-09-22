from setuptools import setup, find_packages

setup(
    name="jev-preflight-director",
    version="2.0.0",
    description="Sub-millisecond Pre-flight Gateway & Director for LLM Agents",
    author="will-xia-cm",
    packages=find_packages(),
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
