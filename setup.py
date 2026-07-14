from setuptools import setup

setup(
    name="dietcode",
    version="0.1.0",
    py_modules=["cli", "db", "parser", "indexer", "graph", "search", "brief"],
    install_requires=[
        "typer",
        "rich",
        "tree-sitter",
        "tree-sitter-python",
        "tree-sitter-javascript",
        "networkx",
        "sentence-transformers",
        "pyfiglet"
    ],
    entry_points={
        "console_scripts": [
            "dietcode=cli:app",
        ]
    }
)
