import logging

import click

from recipe_converter import convert, mela


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s: %(message)s")


cli.add_command(convert.convert)
cli.add_command(mela.mela)
