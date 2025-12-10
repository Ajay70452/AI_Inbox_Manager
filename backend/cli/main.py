"""
Main CLI Entry Point

Command-line interface for AI Inbox Manager
"""

import click
from cli.worker_commands import worker


@click.group()
def cli():
    """AI Inbox Manager - Command Line Interface"""
    pass


# Add command groups
cli.add_command(worker)


if __name__ == '__main__':
    cli()
