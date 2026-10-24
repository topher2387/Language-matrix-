from setuptools import setup, find_packages

setup(
    name="language-matrix",
    version="0.1.0",
    description="A standalone Korean language tutor",
    author="Language Matrix Contributors",
    packages=find_packages(),
    py_modules=["main"],
    python_requires=">=3.8",
    install_requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "language-matrix=main:main",
        ],
    },
)
