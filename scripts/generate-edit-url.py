# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "lzstring",
#     "python-frontmatter",
# ]
# ///
import json
import os
from pathlib import Path

import frontmatter
from lzstring import LZString

URL_PREFIX = "https://shinylive.io/py/editor/#code="
FILES = [
    "paros/index.qmd",
    "visisipy/index.md",
]

REDIRECT_PAGE_TEMPLATE = """
<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url={url}">
        <script type="text/javascript">
            window.location.href = "{url}"
        </script>
        <title>Edit demo code</title>
    </head>
    <body>
        If you are not redirected automatically, follow this link to open the demo in an interactive editor: <a href="{url}">{url}</a>.
    </body>
</html>
"""


def get_shiny_code(contents: str) -> str:
    """
    Extract the shiny code from the contents.
    """
    start_token = "```{shinylive-python}"
    end_token = "```"

    start = contents.find(start_token)
    end = contents.find(end_token, start + len(start_token))

    return contents[start + len(start_token) : end]


def split_code_to_files(code: str) -> dict[str, str]:
    """
    Split the code into separate files based on `## file: ...` comments.
    """
    files = {}
    current_file = None
    current_code: list[str] = []

    for line in code.splitlines():
        if line.startswith("#|"):
            # Skip lines starting with #|
            continue

        if line.startswith("## file: "):
            if len(current_code) > 0 and current_file:
                files[current_file] = "\n".join(current_code)

            current_file = line[len("## file: ") :].strip()
            current_code = []

        else:
            current_code.append(line)

    if current_file:
        files[current_file] = "\n".join(current_code)

    return files


def get_edit_url(file: str) -> str:
    """
    Get the edit URL for the given file.
    """
    path = Path(file)
    contents = path.read_text()
    code = get_shiny_code(contents)
    files = split_code_to_files(code)

    compressed_files = LZString().compressToEncodedURIComponent(
        json.dumps([{"name": k, "content": v} for k, v in files.items()])
    )
    return URL_PREFIX + compressed_files


def write_redirect_file(path: Path, url: str) -> None:
    """
    Write a redirect file to the given path.
    """
    if not path.suffix == ".html":
        raise ValueError("Path must be an HTML file.")

    contents = REDIRECT_PAGE_TEMPLATE.format(url=url)
    path.write_text(contents, encoding="utf-8")


if __name__ == "__main__":
    input_files = os.getenv("QUARTO_PROJECT_INPUT_FILES")
    files = input_files.splitlines() if input_files else FILES

    for file in files:
        path = Path(file)

        settings = frontmatter.load(str(path))

        if settings.get("editable"):
            contents = path.read_text()

            # Extract the shiny code
            code = get_shiny_code(contents)

            if code == "":
                print(f"No shiny code found in {path}. Skipping.")
                continue

            # Split the code into separate files
            code_files = split_code_to_files(code)

            compressed_files = LZString().compressToEncodedURIComponent(
                json.dumps([{"name": k, "content": v} for k, v in code_files.items()])
            )
            url = URL_PREFIX + compressed_files

            write_redirect_file(path.parent / "edit.html", url)

