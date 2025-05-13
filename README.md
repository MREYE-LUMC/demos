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
... # Other frontmatter

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
... # Other frontmatter

editable: true
---
```

This will create an additional html file named `edit.html` in the demo's folder.
To link to the editable demo, a button can be added to the demo's main page:

```markdown
[Edit the demo](edit.html){.btn .btn-outline-primary .btn role="button" .external}
```