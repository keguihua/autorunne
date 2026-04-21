from __future__ import annotations

__all__ = ["app", "__version__"]
__version__ = "0.6.3"


def __getattr__(name: str):
    if name == "app":
        from .cli import app

        return app
    raise AttributeError(name)
