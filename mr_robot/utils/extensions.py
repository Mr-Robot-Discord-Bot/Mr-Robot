import importlib
import inspect
import logging
import pkgutil
from typing import Generator, NoReturn

from mr_robot import exts

logger = logging.getLogger(__name__)

# EXTENSIONS = set()


def unqualify(name: str) -> str:
    """Returns an unqualified name given qualified module/package name"""
    return name.rsplit(".", maxsplit=1)[-1]


def walk_extensions() -> Generator[str, None, None]:
    """Yields extensions name from mr_robot.exts subpackage"""

    def on_error(name: str) -> NoReturn:
        raise ImportError(name=name)

    for module in pkgutil.walk_packages(
        exts.__path__, f"{exts.__name__}.", onerror=on_error
    ):
        if unqualify(module.name).startswith == "_":
            # Ignore module/package names starting with an underscore
            continue
        imported = importlib.import_module(module.name)
        if not inspect.isfunction(getattr(imported, "setup", None)):
            # If that module/package doesn't implement setup function
            logger.warn(f"{module.name} doesn't implement setup function")
            continue
        yield module.name
