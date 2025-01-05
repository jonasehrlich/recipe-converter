import base64
import logging
import pathlib
import random

import click
import primp
from duckduckgo_search import DDGS

from . import melarecipes

_logger = logging.getLogger(__name__)


@click.group(help="Commands working on melarecipes collections.")
def mela():
    pass


IMPERSONATION_OPTIONS = [
    "safari_ios_16.5",
    "safari_ios_17.2",
    "safari_ios_17.4.1",
    "safari_ios_18.1.1",
    "safari_15.3",
    "safari_15.5",
    "safari_15.6.1",
    "safari_16",
    "safari_16.5",
    "safari_17.0",
    "safari_17.2.1",
    "safari_17.4.1",
    "safari_17.5",
    "safari_18",
    "safari_18.2",
    "safari_ipad_18",
    "okhttp_3.9",
    "okhttp_3.11",
    "okhttp_3.13",
    "okhttp_3.14",
    "okhttp_4.9",
    "okhttp_4.10",
    "okhttp_5",
    "edge_101",
    "edge_122",
    "edge_127",
    "edge_131",
    "firefox_109",
    "firefox_133",
]


@mela.command(help="Add images to recipes based on DuckDuckGo image search.")
@click.option("--scale-width", type=int, help="Scale down images to this width.")
@click.argument("input", type=pathlib.Path)
@click.argument("output", type=pathlib.Path)
def add_images(input: pathlib.Path, output: pathlib.Path, scale_width: int | None):
    recipes = list(melarecipes.parse(input))
    client = primp.Client(impersonate=random.choice(IMPERSONATION_OPTIONS), verify=False)

    ddgs = DDGS()
    try:
        for recipe in recipes:
            if recipe.images:
                # We have at least one image, so we don't need to search for more
                _logger.info("Image already present for '%s'", recipe.title)
                continue
            _logger.info("Searching for images for '%s'", recipe.title)
            results = ddgs.images(
                recipe.title,
                type_image="photo",
                size="Large",
                max_results=1,
            )
            if not results:
                _logger.warning("No images found for '%s'", recipe.title)
                continue
            _logger.info("Download image for '%s'", recipe.title)
            try:
                resp = client.get(results[0]["image"])
                recipe.images.append(base64.b64encode(resp.content).decode())
            except Exception as exc:
                _logger.error("Failed to download image for '%s': %s", recipe.title, exc)
                continue

    finally:
        melarecipes.write(output, recipes)
