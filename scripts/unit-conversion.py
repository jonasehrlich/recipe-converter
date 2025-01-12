#! /usr/bin/env python3
import argparse
import pathlib
import re
from typing import Literal

from recipe_converter import melarecipes

MULTI_SPACE_PATTERN = re.compile(r"\s+")
# https://www.wedesoft.de/software/2020/07/07/mealmaster/
UNIT_CONVERSIONS = {
    "dr": "Tropfen",
    "ds": "Spritzer",
    "bn": "Bund",
    "sm": "Kleine",
    "md": "Mittlere",
    "lg": "Große",
    "St": "",
    "Sk": "",
    "cn": "Dose",
    "pn": "Prise",
    "fl": "fl. oz.",
    "tbsp": "EL",
    "tsp": "TL",
    "c": "Tasse",
    "pk": "Pkg",
    "sl": "Scheibe",
    "Ms": "Msp",
}

UNIT_CONVERSIONS = {f" {key} ": f" {value} " for key, value in UNIT_CONVERSIONS.items()}


def input_with_default(_prompt: str, default: str | None) -> str:
    """Prompt for a user input and return a default value on empty input

    :param _prompt: Prompt to write to stdout
    :param default: Default value
    :return: User input or default value
    """
    resp = input(_prompt + " ")
    if default and not resp:
        resp = default
    return resp


def confirm(prompt_: str, default: Literal["y", "n"] | None = None) -> bool:
    if default == "y":
        options = "(Y/n)"
    elif default == "n":
        options = "(y/N)"
    elif default is None:
        options = "(y/n)"

    resp = input_with_default(f"{prompt_} {options}", default)
    if resp.upper() == "Y":
        return True
    elif resp.upper() == "N":
        return False
    else:
        if resp.upper():
            print(f"Invalid input: '{resp}'")
        return confirm(prompt_, default)


def main():
    parser = argparse.ArgumentParser(
        description="Convert units used in ingredients of melarecipes collections from Meal-Master format to a Mela compatible one."
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
    parser.add_argument(
        "--confirm-all",
        "-y",
        action="store_true",
        help="Automatically confirm all prompts.",
    )
    namespace = parser.parse_args()
    recipes = list(melarecipes.parse(namespace.input))
    try:
        for recipe in recipes:
            if any((s in recipe.link for s in ("bonappetit", "halfbakedharvest", "Lea Ehrlich"))):
                print(f"Skipping '{recipe.title}'")
                continue

            ingredients = recipe.ingredients.split("\n")
            end = "\n" if namespace.confirm_all else ""
            for idx, ingredient in enumerate(ingredients):
                for unit, conversion in UNIT_CONVERSIONS.items():
                    new_ingredient = ingredient.replace(unit, conversion)
                    if new_ingredient != ingredient:
                        new_ingredient = MULTI_SPACE_PATTERN.sub(" ", new_ingredient.strip())
                        print(f"Update unit of '{recipe.title}' from '{ingredient}' to '{new_ingredient}'", end=end)
                        if namespace.confirm_all or confirm(" Confirm?", default="y"):
                            ingredients[idx] = new_ingredient
            recipe.ingredients = "\n".join(ingredients)
    finally:
        melarecipes.write(namespace.output, recipes)


if __name__ == "__main__":
    main()
