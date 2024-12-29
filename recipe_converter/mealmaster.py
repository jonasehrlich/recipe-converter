import re
import io
import dataclasses
import collections.abc
from typing import TextIO


@dataclasses.dataclass
class IngredientsGroup:
    title: str
    ingredients: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Recipe:
    title: str = ""
    servings: str = ""
    categories: list[str] = dataclasses.field(default_factory=list)
    ingredients_groups: list[IngredientsGroup] = dataclasses.field(default_factory=list)
    instructions: str = ""


class Patterns:
    START_RECIPE = re.compile(r"MMMMM(-)+.*\n")
    END_RECIPE = re.compile(r"MMMMM\n")
    SUBHEADING = re.compile(r"MMMMM(-)+.*-+\n")

    TITLE_LINE = re.compile(r"^\s*Title:\s*(.+)", re.MULTILINE)
    CATEGORIES_LINE = re.compile(r"^\s*Categories:\s*(.+)", re.MULTILINE)
    SERVINGS_LINE = re.compile(r"^\s*Servings:\s*(.+)", re.MULTILINE)

    COMMENT_LINE = re.compile(r"^::(.+)", re.MULTILINE)
    MULTI_SPACE = re.compile(r"\s+")


def _parse_header(recipe: Recipe, f: TextIO) -> None:
    """Parse the header of a Meal-Master recipe.

    Generally the header contains the title, categories, and servings.

    ::
        Title: Flammendes Wikingerschwert
        Categories: Fleisch
        Servings: 4 Portionen

    :param recipe: Recipe object to update.
    :param f: file-like object to read from.
    """
    started = False

    for line in f:
        if not line.strip():
            if started:
                break
            else:
                continue
        title_match = Patterns.TITLE_LINE.match(line)
        if title_match:
            recipe.title = title_match.group(1).title()
            started = True
            continue

        categories_match = Patterns.CATEGORIES_LINE.match(line)
        if categories_match:
            recipe.categories = [
                category.strip() for category in categories_match.group(1).split(",")
            ]
            started = True
            continue

        servings_match = Patterns.SERVINGS_LINE.match(line)
        if servings_match:
            recipe.servings = servings_match.group(1)
            started = True
            continue


def _parse_ingredients_groups(buffer: io.StringIO) -> list[IngredientsGroup]:
    """Parse the ingredient groups from the ingredients section of a Meal-Master recipe.

    :param lines: _description_
    :return: List of ingredient groups
    """
    ingredients_group: IngredientsGroup | None = None
    ingredients_groups = []
    for line in buffer:
        if not line.strip():
            if ingredients_group is not None:
                # We are at the end of the ingredients, so we need to add the current group to the list.
                ingredients_groups.append(ingredients_group)
                ingredients_group = None
            break
        subheading_match = Patterns.SUBHEADING.match(line)
        if subheading_match:
            if ingredients_group:
                # We are not at the beginning of the file, so we need to add the previous group to the list.
                ingredients_groups.append(ingredients_group)
            ingredients_group = IngredientsGroup(title=subheading_match.group(1))
            continue
        if not ingredients_group:
            # We are at the beginning of the file, so we need to create a default group.
            ingredients_group = IngredientsGroup(title="Ingredients")
        stripped_line = Patterns.MULTI_SPACE.sub(" ", line.strip())
        if stripped_line.startswith("-"):
            # This line is a continuation of the previous ingredient.
            if not ingredients_group.ingredients:
                # There is no previous ingredient to continue.
                ingredients_group.ingredients.append(stripped_line[2:])
            else:
                ingredients_group.ingredients[-1] += " "
                ingredients_group.ingredients[-1] += stripped_line[2:]
            continue

        ingredients_group.ingredients.append(stripped_line)

    if ingredients_group is not None:
        # We are at the end of the ingredients, so we need to add the current group to the list.
        ingredients_groups.append(ingredients_group)
    return ingredients_groups


def _parse_ingredients(buffer: TextIO) -> list[IngredientsGroup]:
    ingredients_buffer = io.StringIO()
    for line in buffer:
        if not line.strip():
            break
        ingredients_buffer.write(line)
    ingredients_buffer.seek(0)
    return _parse_ingredients_groups(ingredients_buffer)


def _parse_recipe(buffer: TextIO) -> Recipe:
    """Parse a Meal-Master recipe.

    :param f: File-like object to read from.
    :return: Recipe object.
    """
    recipe = Recipe()
    try:
        _parse_header(recipe, buffer)
    except Exception as exc:
        buffer.seek(0)
        raise ValueError(f"Error parsing header of recipe {buffer.readline()}") from exc

    try:
        recipe.ingredients_groups = _parse_ingredients(buffer)
    except Exception as exc:
        raise ValueError(f"Error parsing ingredients of recipe {recipe.title}") from exc

    instructions = io.StringIO()
    for line in buffer:
        if Patterns.COMMENT_LINE.match(line):
            continue
        instructions.write(line)
    instructions.seek(0)
    recipe.instructions = instructions.read().strip()

    return recipe


def parse(f: TextIO) -> collections.abc.Generator[Recipe, None, None]:
    recipe_started = False
    # Buffer for the text of the current recipe.
    recipe_buffer = io.StringIO()
    for line in f:
        if Patterns.START_RECIPE.match(line):
            recipe_started = True
            continue
        if recipe_started and Patterns.END_RECIPE.match(line):
            recipe_started = False
            recipe_buffer.seek(0)
            yield _parse_recipe(recipe_buffer)
            recipe_buffer = io.StringIO()
            continue
        if recipe_started:
            recipe_buffer.write(line)
