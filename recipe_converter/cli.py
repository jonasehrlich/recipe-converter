import argparse
import pathlib
from typing import Protocol
from recipe_converter import mealmaster, melarecipes
import sys


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


def get_arg_parser():
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
    return parser


def run_converter(input: pathlib.Path, output: pathlib.Path):
    for converter_input_suffix, converter_output_suffix, converter in CONVERTERS:
        if (
            input.suffix == converter_input_suffix
            and output.suffix == converter_output_suffix
        ):
            converter(input, output)
            return
    raise ValueError(f"No converter found from {input.suffix} to {output.suffix}")


def main():
    parser = get_arg_parser()
    namespace = parser.parse_args()

    try:
        run_converter(namespace.input, namespace.output)
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
