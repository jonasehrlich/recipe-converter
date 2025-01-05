import pathlib
from typing import Protocol

import click

from . import mealmaster, melarecipes


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


CONVERTERS: tuple[tuple[str, str, Converter], ...] = ((".mmf", ".melarecipes", mealmaster_to_melarecipes),)


@click.command(help="Convert recipe collections between different formats.")
@click.argument("input", type=pathlib.Path)
@click.argument("output", type=pathlib.Path, required=True)
def convert(input: pathlib.Path, output: pathlib.Path):
    for converter_input_suffix, converter_output_suffix, converter in CONVERTERS:
        if input.suffix == converter_input_suffix and output.suffix == converter_output_suffix:
            try:
                converter(input, output)
            except Exception as exc:
                raise click.BadParameter(f"Error converting {input} to {output}: {exc}")
            return
    raise click.BadParameter(f"No converter found from {input.suffix} to {output.suffix}")
