from setuptools import setup

setup(
    name="color-cli",
    version="1.0.0",
    py_modules=["color"],
    entry_points={
        "console_scripts": [
            "color=color:main",
        ],
    },
    python_requires=">=3.8",
)
