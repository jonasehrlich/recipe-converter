import pydantic
import uuid
import pathlib
import re
import zipfile
import hashlib
import pydantic.alias_generators
import collections.abc


class Recipe(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    id: str = pydantic.Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Identifier. For recipes imported from the web, Mela uses the URL (without schema) as identifier, otherwise just a UUID. If you're creating a melarecipe file for importing, make sure this is not empty.",
    )
    title: str = pydantic.Field(description="Title of the recipe")
    text: str = pydantic.Field(
        default="",
        description="Short description of the recipe which is displayed after the title and info in Mela. Supported: Markdown: Links.",
    )
    images: list[str] = pydantic.Field(
        default_factory=list, description="Array of base64 encoded images."
    )
    categories: list[str] = pydantic.Field(
        default_factory=list,
        description="Array of category names. Please: note that Mela currently does not allow , in a category name.",
    )
    yield_: str = pydantic.Field(
        default="", alias=str("yield"), description="Yield or servings"
    )
    prep_time: str = pydantic.Field(
        default="", alias=str("prepTime"), description="Preparation time"
    )
    cook_time: str = pydantic.Field(
        default="", alias=str("cookTime"), description="Cook time"
    )
    total_time: str = pydantic.Field(
        default="",
        alias=str("totalTime"),
        description="Total time it takes to prepare and cook the dish. This: does not have to be the sum of prepTime and cookTime (but mostly is).",
    )
    ingredients: str = pydantic.Field(
        default="",
        description="Ingredients, separated by \n. Supported: Markdown: Links and # for group titles.",
    )
    instructions: str = pydantic.Field(
        default="",
        description="Instructions, separated by \n. Supported: Markdown: # * ** and links.",
    )
    notes: str = pydantic.Field(
        default="",
        description="The notes that are displayed right after the instructions in Mela. Supported: Markdown: # * ** and links.",
    )
    nutrition: str = pydantic.Field(
        default="",
        description="Nutrition information. Supported: Markdown: # * ** and links.",
    )
    link: str = pydantic.Field(
        default="",
        description="This might be a bit misleading but this field does not have to contain an URL (it can). It's basically just the source of the recipe and will accept any str.",
    )

    def filename(self) -> pathlib.Path:
        cleaned_str = re.sub(r"[^a-zA-Z0-9\s]", "", self.title)
        kebap_str = cleaned_str.replace(" ", "-").lower()
        return pathlib.Path(
            f"{kebap_str}-{hashlib.sha256(self.id.encode()).hexdigest()[:6]}.melarecipe"
        )


def write(path: pathlib.Path, recipes: list[Recipe]) -> None:
    ta = pydantic.TypeAdapter(Recipe)
    with zipfile.ZipFile(path, "w") as zip_file:
        for recipe in recipes:
            zip_file.writestr(
                str(recipe.filename()), ta.dump_json(recipe, by_alias=True)
            )


def parse(path: pathlib.Path) -> collections.abc.Generator[Recipe]:
    with zipfile.ZipFile(path, "r") as archive:
        for filename in archive.namelist():
            with archive.open(filename) as file:
                yield Recipe.model_validate_json(file.read())
