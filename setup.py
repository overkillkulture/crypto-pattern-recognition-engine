from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="crypto-pattern-recognition-engine",
    version="0.1.0",
    author="OverkillKulture",
    description="World-class cryptocurrency pattern recognition and analysis engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/overkillkulture/crypto-pattern-recognition-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "ccxt>=4.0.0",
        "ta-lib>=0.4.28",
        "scikit-learn>=1.3.0",
        "pyyaml>=6.0",
        "loguru>=0.7.0",
        "fastapi>=0.108.0",
    ],
    entry_points={
        "console_scripts": [
            "crypto-pattern=src.cli:main",
        ],
    },
)
