# MReye demos

Interactive demos for research projects of the MReye group.

Current demos:

- PAROS
- Visisipy

Demos are built using [Shiny for Python](https://shiny.posit.co/py/) and embedded in a [Quarto](https://quarto.org/) website using [Shinylive](https://github.com/posit-dev/shinylive).

## Development

> [!NOTE]
> As all demos are developed in Python, dependencies are managed using [`uv`](https://astral.sh/uv).
> You can use WinGet to install `uv` on Windows:
> 
>  ```powershell
>  winget install astral-sh.uv
>  ```
> On Linux and MacOS, use
> 
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```

1. Clone this repository or open it in a Codespace
2. Install the dependencies:
    ```bash
    uv sync
    ```
3. Make your changes
4. Run the preview:
    ```bash
    uv run quarto preview
    ```
    The preview will be updated automatically as you make changes.
5. Push your changes. They will be automatically deployed to GitHub Pages.

## MDR message

Every demo must warn the user that these demos are not intended for medical use.
To do this, add the following to the demo's frontmatter:

```markdown
---
# Other frontmatter

format:
  html:
    include-after-body: ../_includes/mdr-modal.html # Note: this path is relative to the demo's folder
---
```


## Editable demos

URLs to demos that can be edited on <shinylive.io> are automatically generated when rendering the website.
To enable this feature for a demo, add the following to the demo's frontmatter:

```markdown
---
# Other frontmatter

editable: true
---
```

This will create an additional html file named `edit.html` in the demo's folder.
To link to the editable demo, a button can be added to the demo's main page:

```markdown
[Edit the demo](edit.html){.btn .btn-outline-primary .btn role="button" .external}
```

## Custom wheels

Shinylive uses [Pyodide](https://pyodide.org/en/stable/) to run Python code in the browser.
Visisipy depends on Optiland, which depends on VTK and Numba.
These libraries are not available in the default Pyodide distribution.
To be able to run visisipy and Optiland in the browser, we use custom libraries that mock the functionality needed by Optiland.

- For Numba, the necessary decorators are mocked and return the decorated function as is. The `prange` function is replaced with `range`.
- The mock library for VTK raises an exception when trying to access any of its members.
  Importing it works and allows Optiland to run, but any Optiland functionality that depends on VTK will raise an exception.

The code for the mock libraries is located in `visisipy/custom_wheels/`.
Wheels for these libraries can be built using `visisipy/custom_wheels/build_wheels.py`.
This builds the libraries and copies the wheels to the `_assets` folder.

```bash
uv run visisipy/custom_wheels/build_wheels.py
```

Building the wheels is only necessary when the code in `visisipy/custom_wheels/` has been changed.
URLs to the wheels should be added under `## file: requirements.txt` in the demo code, and above `visisipy`.