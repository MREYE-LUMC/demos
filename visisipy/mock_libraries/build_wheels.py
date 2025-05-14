"""Build wheels and copy them to the assets directory."""

from subprocess import run
from pathlib import Path
from warnings import warn
from shutil import copy2

def build_wheel(path: Path) -> None:
    """
    Build the wheel for the current package.
    """
    # Run the command to build the wheel
    run(["uv", "build", "."], cwd=path, check=True)


def get_wheel_path(path: Path) -> Path:
    """
    Get the path to the wheel file.
    """
    dist = path / "dist"
    wheels = list(dist.glob("*.whl"))

    if not wheels:
        raise FileNotFoundError("No wheel file found in the dist directory.")
    if len(wheels) > 1:
        warn("Multiple wheel files found in the dist directory. Returning the newest one.")

    # Sort wheels by modification time
    wheels.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    return wheels[0]


if __name__ == "__main__":
    # Get the path to the current directory
    path = Path(__file__).parent
    repository_root = path.parent.parent

    libraries = [d for d in path.iterdir() if d.is_dir() and (d / "pyproject.toml").exists()]

    for library in libraries:
        build_wheel(library)

        wheel_path = get_wheel_path(library)

        # Copy the wheel to the assets directory
        copy2(wheel_path, repository_root / "_assets" / "wheels")
