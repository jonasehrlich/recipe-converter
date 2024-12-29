import argparse
import pathlib
from typing import Protocol


class Converter(Protocol):
    def __call__(self, input: pathlib.Path, output: pathlib.Path) -> None: ...


def mealmaster_to_mela(input: pathlib.Path, output: pathlib.Path):
    from recipe_converter import mealmaster
    with input.open("r") as file:
        recipes = mealmaster.parse(file)
        print(next(recipes))



CONVERTERS: tuple[tuple[str, str, Converter], ...] = (
    (".mmf", ".melarecipes", mealmaster_to_mela),
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
    raise ValueError("No converter found for the specified input and output formats.")


def main():
    parser = get_arg_parser()
    namespace = parser.parse_args()

    try:
        run_converter(namespace.input, namespace.output)
    except Exception as exc:
        parser.error(str(exc))
