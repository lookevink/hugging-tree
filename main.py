import typer
import os
import time

app = typer.Typer()

@app.command()
def scan():
    """
    Scan the repository for changes.
    """
    print("Scanning repository...")
    # TODO: Implement scan logic

@app.command()
def parse():
    """
    Parse the changed files.
    """
    print("Parsing files...")
    # TODO: Implement parse logic

if __name__ == "__main__":
    app()
