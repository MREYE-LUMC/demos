# MReye demos

Interactive demos for research projects of the MReye group.

Current demos:

- PAROS
- Visisipy

Demos are built using [Shiny for Python](https://shiny.posit.co/py/) and embedded in an [Astro](https://astro.build/) website using [Shinylive](https://github.com/posit-dev/shinylive).

## Dependencies

The demos are developed in Python using shinylive.
The website is built using Astro.
For development, both Node.js (and `npm`) and Python with `uv` are required.
The website build process requires `uv` to generate the Shinylive assets.

## Project structure

- Shiny demos are located in `demos/<demo name>/`. Each demo consists of at least two files: `app.py` with the demo and `requirements.txt` with the dependencies.
- The website is located in `src`. Demo pages are put in `src/demos/<demo name>.mdx`.
- `tests/` contains smoke tests that check if the demos are rendered successfully.

> [!NOTE]
> The subfolder name in `demos/` and the file name in `src/demos/` should be the same, as these are used to link the demo to the web page.

## Demo development

> [!NOTE]
> As all demos are developed in Python, dependencies are managed using [`uv`](https://astral.sh/uv).
> You can use WinGet to install `uv` on Windows:
>
> ```powershell
> winget install astral-sh.uv
> ```
>
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
4. Preview the demo:
   ```bash
   uv run shiny run -r demos/<demo-name>/app.py
   ```
   The `-r` flag enables reloading on save, so the preview will be updated if you change `app.py`.
5. Push your changes. They will be automatically deployed to GitHub Pages.

> [!IMPORTANT]
> Do not include additional non-required files in the demo folders! All files will be bundled in the shinylive assets, not only the files used by the demo.

## Website development

1. Clone this repository or open it in a Codespace
2. Install the dependencies:
   ```bash
   npm i
   ```
3. Make your changes
4. Preview the website:

   ```bash
   npm run dev
   ```

   The dev server will not render the demos themselves. If you want to include the demos, build the website and then preview it:

   ```bash
   npm run build
   npm run preview
   ```

5. Push your changes. They will be automatically deployed to GitHub Pages

This is the structure of a demo page in `src/demos`:

```md
---
# title displayed on the demo page
title: "Calculate the central magnification of an eye - camera system"
# Name used on the home page and in the navigation bar
name: PAROS
# Description displayed on the home page
description: Calculate the central magnification of fundus photographs using an analytical method.
# URL of the repository of the demonstrated code (optional)
repoUrl: https://github.com/MREYE-LUMC/PAROS
# URL of the paper linked to the demonstrated research (optional)
paperUrl: https://doi.org/10.1167/iovs.65.1.43

# Order on the home page and in the navigation bar
weight: 0
---

<!-- Import this if you want to show a note or warning message -->

import Callout from "../components/Callout.astro";

This integration demonstrates how PAROS can be used to calculate the central magnification of a fundus image.
More information can be found at our [GitHub repository](https://github.com/MREYE-LUMC/PAROS).

<Callout title="Warning" type="warning">
This example is not intended for medical use and does not allow to customize camera-related parameters.
</Callout>

To calculate the magnification of a fundus image, enter the parameters of the eye in the calculator below.
If you do not have all required parameters, it is possible to estimate some parameters:

- The posterior corneal curvature can be estimated as 0.81 x anterior corneal curvature.
  To do this, click the **Estimate posterior corneal curvature** button.
- The posterior lens curvature can be fitted from the spherical equivalent of refraction.
  To do this, click the **Fit posterior lens curvature** button.
```

## Custom wheels

Shinylive uses [Pyodide](https://pyodide.org/en/stable/) to run Python code in the browser.
Visisipy depends on Optiland, which depends on VTK and Numba.
These libraries are not available in the default Pyodide distribution.
To be able to run visisipy and Optiland in the browser, we use custom libraries that mock the functionality needed by Optiland.

- For Numba, the necessary decorators are mocked and return the decorated function as is. The `prange` function is replaced with `range`.
- The mock library for VTK raises an exception when trying to access any of its members.
  Importing it works and allows Optiland to run, but any Optiland functionality that depends on VTK will raise an exception.

The code for the mock libraries is located in `mock_libraries/`.
Wheels for these libraries can be built using `mock_libraries/build_wheels.py`.
This builds the libraries and copies the wheels to the `public/_assets` folder.

```bash
uv run mock_libraries/build_wheels.py
```

Building the wheels is only necessary when the code in `mock_libraries/` has been changed.
URLs to the wheels should be added in `demos/visisipy/requirements.txt`, and above `visisipy`.
