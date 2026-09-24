from setuptools import setup, find_packages

setup(
    name="jev-preflight-director",
    version="2.2.0",
    description="High-speed preflight director, task preloader, and cognitive operating system for LLM Agents",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="dl013209-ai",
    url="https://github.com/dl013209-ai/jev-preflight-director",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
