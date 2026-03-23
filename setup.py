from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lingminopt",
    version="0.1.0",
    author="Guangda",
    description="LingMinOpt - A universal minimalist self-optimization framework inspired by 灵研",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lingminopt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "click>=8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "isort>=5.0",
            "mypy>=0.950",
        ],
        "visualization": [
            "matplotlib>=3.5.0",
            "seaborn>=0.12.0",
        ],
        "bayesian": [
            "scipy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lingminopt=lingminopt.cli.commands:cli",
        ],
    },
)
