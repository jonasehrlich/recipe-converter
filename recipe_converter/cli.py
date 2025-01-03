import argparse
import base64
import logging
import pathlib
import random
import sys
from typing import Protocol

import primp
from duckduckgo_search import DDGS

from recipe_converter import mealmaster, melarecipes

_logger = logging.getLogger(__name__)


class Converter(Protocol):
    def __call__(self, input: pathlib.Path, output: pathlib.Path) -> None: ...


def mealmaster_to_melarecipe(mm_recipe: mealmaster.Recipe) -> melarecipes.Recipe:
    """Convert a Meal-Master recipe to a Mela recipe."""
    ingredients = ""
    for group in mm_recipe.ingredients_groups:
        if group.title:
            ingredients += f"# {group.title}\n"
        ingredients += f"{'\n'.join(group.ingredients)}\n"

    melarecipe = melarecipes.Recipe(
        title=mm_recipe.title,
        text=mm_recipe.description,
        categories=mm_recipe.categories,
        yield_=mm_recipe.servings,
        ingredients=ingredients,
        instructions=mm_recipe.instructions,
        nutrition=mm_recipe.nutrition,
        cook_time=mm_recipe.cook_time,
        prep_time=mm_recipe.prep_time,
        total_time=mm_recipe.total_time,
        notes=mm_recipe.notes,
        link=mm_recipe.source,
    )
    return melarecipe


def mealmaster_to_melarecipes(input: pathlib.Path, output: pathlib.Path):
    with input.open("r") as file:
        mm_recipes = mealmaster.parse(file)
        mela_recipes = []

        for mm_recipe in mm_recipes:
            mela_recipes.append(mealmaster_to_melarecipe(mm_recipe))

        print("Parsed and converted", len(mela_recipes), "recipes")
        melarecipes.write(output, mela_recipes)


CONVERTERS: tuple[tuple[str, str, Converter], ...] = (
    (".mmf", ".melarecipes", mealmaster_to_melarecipes),
)


def convert():
    parser = argparse.ArgumentParser(
        description="Convert recipes between different formats."
    )
    parser.add_argument(
        "input",
        type=pathlib.Path,
        help="Path to the input file to convert.",
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        help="Path to save the converted output.",
    )
    namespace = parser.parse_args()

    for converter_input_suffix, converter_output_suffix, converter in CONVERTERS:
        if (
            namespace.input.suffix == converter_input_suffix
            and namespace.output.suffix == converter_output_suffix
        ):
            try:
                converter(namespace.input, namespace.output)
            except Exception as exc:
                print(f"Error: {exc}")
                sys.exit(1)
            sys.exit(0)
    raise ValueError(
        f"No converter found from {namespace.input.suffix} to {namespace.output.suffix}"
    )


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


def melarecipes_add_images():
    parser = argparse.ArgumentParser(description="Add images to a Mela collection")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "input",
        type=pathlib.Path,
        help="Path to the input file to convert.",
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        help="Path to save the converted output.",
    )

    namespace = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if namespace.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    recipes = list(melarecipes.parse(namespace.input))
    client = primp.Client(
        impersonate=random.choice(IMPERSONATION_OPTIONS), verify=False
    )

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
        melarecipes.write(namespace.output, recipes)
