import collections.abc
import dataclasses
import io
import re
from typing import TextIO


@dataclasses.dataclass
class IngredientsGroup:
    title: str
    ingredients: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Recipe:
    title: str = ""
    description: str = ""
    servings: str = ""
    cook_time: str = ""
    prep_time: str = ""
    total_time: str = ""
    total_time: str = ""
    categories: list[str] = dataclasses.field(default_factory=list)
    ingredients_groups: list[IngredientsGroup] = dataclasses.field(default_factory=list)
    instructions: str = ""
    nutrition: str = ""
    source: str = ""
    notes: str = ""


class Patterns:
    START_RECIPE = re.compile(r"MMMMM(-)+.*\n")
    END_RECIPE = re.compile(r"MMMMM\n")
    SUBHEADING = re.compile(r"MMMMM(-)+.*-+\n")

    TITLE_LINE = re.compile(r"^\s*Title:\s*(.+)", re.MULTILINE)
    CATEGORIES_LINE = re.compile(r"^\s*Categories:\s*(.+)", re.MULTILINE)
    SERVINGS_LINE = re.compile(r"^\s*Servings:\s*(.+)", re.MULTILINE)
    PREP_TIME_LINE = re.compile(r"^\s*Prep(?:aration)? Time:\s*(.+)", re.MULTILINE | re.IGNORECASE)
    COOK_TIME_LINE = re.compile(r"^\s*Cook(?:ing)? Time:\s*(.+)", re.MULTILINE | re.IGNORECASE)
    TOTAL_TIME_LINE = re.compile(r"^\s*Total Time:\s*(.+)", re.MULTILINE | re.IGNORECASE)
    DESCRIPTION = re.compile(r"^\s*Description?:\s*(.+)", re.MULTILINE | re.IGNORECASE)
    NOTES_LINE = re.compile(r"^\s*Notes?:\s*(.+)", re.MULTILINE | re.IGNORECASE)

    SOURCE_COMMENT_LINE = re.compile(r"^::Quelle\s+:\s+:\s+(.+)", re.MULTILINE | re.IGNORECASE)
    CATEGORIES_COMMENT_LINE = re.compile(r"^::Stichworte\s+:\s+:\s(.+)", re.MULTILINE | re.IGNORECASE)
    NUTRITIONAL_LINE = re.compile(r"^::Energie\s+:\s+:\s(.+)", re.MULTILINE | re.IGNORECASE)
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
            recipe.categories = [category.strip() for category in categories_match.group(1).split(",")]
            started = True
            continue

        servings_match = Patterns.SERVINGS_LINE.match(line)
        if servings_match:
            recipe.servings = servings_match.group(1)
            started = True
            continue

        prep_time_match = Patterns.PREP_TIME_LINE.match(line)
        if prep_time_match:
            started = True
            recipe.prep_time = prep_time_match.group(1)
            continue

        cook_time_match = Patterns.COOK_TIME_LINE.match(line)
        if cook_time_match:
            started = True
            recipe.cook_time = cook_time_match.group(1)
            continue

        total_time_match = Patterns.TOTAL_TIME_LINE.match(line)
        if total_time_match:
            started = True
            recipe.total_time = total_time_match.group(1)
            continue

        description_match = Patterns.DESCRIPTION.match(line)
        if description_match:
            started = True
            recipe.description = description_match.group(1)
            continue

        note_match = Patterns.NOTES_LINE.match(line)
        if note_match:
            started = True
            if recipe.notes:
                recipe.notes += "\n"
            recipe.notes += note_match.group(1)
            continue


def _parse_ingredients_groups(buffer: io.StringIO) -> list[IngredientsGroup]:
    """Parse the ingredient groups from the ingredients section of a Meal-Master recipe.
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
            ingredients_group = IngredientsGroup(title="")
        stripped_line = Patterns.MULTI_SPACE.sub(" ", line.strip())
        if stripped_line.startswith("-"):
            # Mealmaster only supports a limited line length for ingredients. Longer lines are continued with a '-' character.
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
        nutrition_match = Patterns.NUTRITIONAL_LINE.match(line)
        if nutrition_match:
            recipe.nutrition = nutrition_match.group(1)
            continue

        categories_comment_match = Patterns.CATEGORIES_COMMENT_LINE.match(line)
        if categories_comment_match:
            for cat in categories_comment_match.group(1).split():
                cat = cat.replace(",", "")
                if cat not in recipe.categories:
                    recipe.categories.append(cat)
            continue

        source_comment_match = Patterns.SOURCE_COMMENT_LINE.match(line)
        if source_comment_match and not recipe.source:
            recipe.source = source_comment_match.group(1)
            continue

        if Patterns.COMMENT_LINE.match(line):
            continue
        instructions.write(line)
    instructions.seek(0)
    recipe.instructions = instructions.read().strip().replace("\n\n", "\n")

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
