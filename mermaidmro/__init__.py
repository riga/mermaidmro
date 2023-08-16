# coding: utf-8
# flake8: noqa

from __future__ import annotations

__all__ = [
    "get_mermaid_text",
    "get_style_text",
    "get_relations",
    "encode_text",
    "encode_json",
    "download_graph",
]

import os
import zlib
import base64
import json
import importlib
import fnmatch
import collections
from typing import Callable

# package infos
from mermaidmro.__version__ import (
    __doc__,
    __author__,
    __email__,
    __copyright__,
    __credits__,
    __contact__,
    __license__,
    __status__,
    __version__,
)


# mermaid endpoints
URL_STATIC = "https://mermaid.ink/img/{}?type={}"
URL_STATIC_JSON = "https://mermaid.ink/img/pako:{}?type={}"
URL_EDIT_JSON = "https://mermaid.live/edit#pako:{}"

#: Relation between two classes including a depth value with respect to the requested root class.
Relation = collections.namedtuple("Relation", ["cls", "base_cls", "root_depth"])

#: TODO.
Style = collections.namedtuple("Style", ["name", "cls", "attributes"])


def get_relations(
    root_cls: type,
    max_depth: int = -1,
) -> list[Relation]:
    """
    Resolve parameter values *params* from command line and propagate them to this set of
    parameters.

    :param params: Parameters provided at command line level.
    :return: Updated list of parameter values.
    """
    # stop early
    if max_depth == 0:
        return []

    # iterate recursively with lookup pattern
    lookup = [(root_cls, 0)]
    seen = set()
    relations = []
    while lookup:
        cls, depth = lookup.pop(0)

        # skip when cls already handled
        if cls in seen:
            continue

        # handle base classes
        for base_cls in cls.__bases__:
            # add class relation, starting at depth 1
            relations.append(Relation(cls, base_cls, depth + 1))

            # ammend lookup when depth below maximum
            if max_depth < 0 or depth + 1 < max_depth:
                lookup.append((base_cls, depth + 1))

        # mark as seen
        seen.add(cls)

    return relations


def get_default_name_func(
    skip_modules: list[str] | set[str] | None = None,
) -> Callable[[type], str]:
    # default list of module names to skip
    skip_modules = set(skip_modules or [])

    # always skip certain modules
    skip_modules |= {"builtins", "__main__"}

    def name_func(cls: type) -> str:
        if isinstance(cls, str):
            return cls

        if cls.__module__ and not any(fnmatch.fnmatch(cls.__module__, m) for m in skip_modules):
            return f"{cls.__module__}.{cls.__qualname__}"

        return cls.__qualname__

    return name_func


def get_style_text(
    styles: list[Style | tuple],
    indentation: str = "    ",
    name_func: Callable[[type], str] | None = None,
    skip_modules: list[str] | set[str] | None = None,
    join_lines: bool = True,
) -> str | list[str]:
    """
    TODO.
    """
    # default name_func
    if name_func is None:
        name_func = get_default_name_func(skip_modules=skip_modules)

    # ensure styles is a list of style objects
    styles = [
        style if isinstance(style, Style) else Style(*style)
        for style in styles
    ]

    # style definitions
    lines = []
    for style in styles:
        attr_str = (
            style.attributes
            if isinstance(style.attributes, str)
            else ", ".join(style.attributes)
        )
        lines.append(f"{indentation}classDef {style.name} {attr_str}")

    # empty line
    lines.append("")

    # class assignments
    for style in styles:
        classes = style.cls if isinstance(style.cls, (list, tuple, set)) else [style.cls]
        for cls in classes:
            lines.append(f"{indentation}class {name_func(cls)} {style.name}")

    # join or return as list of lines
    return "\n".join(lines) if join_lines else lines


def get_mermaid_text(
    root_cls: type,
    max_depth: int = -1,
    graph_type: str = "TD",
    arrow_type: str = "-->",
    indentation: str = "    ",
    styles: list[Style | tuple] | None = None,
    skip_func: Callable[[type, Callable], bool] | None = None,
    name_func: Callable[[type], str] | None = None,
    skip_modules: list[str] | set[str] | None = None,
    join_lines: bool = True,
) -> str | list[str]:
    """
    TODO.
    """
    # default name_func
    if name_func is None:
        name_func = get_default_name_func(skip_modules=skip_modules)

    # build lines
    lines = [f"graph {graph_type}"]

    # add relations
    for rel in get_relations(root_cls, max_depth=max_depth):
        # potentially skip
        if callable(skip_func) and skip_func(rel.base_cls, name_func):
            continue

        # add line
        lines.append(f"{indentation}{name_func(rel.base_cls)} {arrow_type} {name_func(rel.cls)}")

    # add styles
    if styles:
        # add lines
        lines.append("")
        lines.extend(get_style_text(
            styles,
            indentation=indentation,
            name_func=name_func,
            join_lines=False,
        ))

    # join or return as list of lines
    return "\n".join(lines) if join_lines else lines


def encode_text(
    mermaid_text: str,
) -> str:
    """
    TODO.
    """
    return base64.urlsafe_b64encode(mermaid_text.encode("utf-8")).decode("utf-8")


def encode_json(
    mermaid_text: str,
    theme: str | None = "default",
) -> str:
    """
    TODO.
    """
    data = json.dumps({
        "code": mermaid_text,
        "mermaid": json.dumps({"theme": theme} if theme else {}),
    })
    return base64.urlsafe_b64encode(zlib.compress(data.encode("utf-8"), level=9)).decode("utf-8")


def download_graph(
    mermaid_text: str,
    path: str,
    file_type: str = "jpg",
) -> str:
    """
    TODO.
    """
    import requests

    # normalize path
    path = os.path.normpath(os.path.expandvars(os.path.expanduser(path)))

    # ensure parent directory exists
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)

    # download and write
    with open(path, "wb") as f:
        url = URL_STATIC_JSON.format(encode_json(mermaid_text), file_type)
        r = requests.get(url, allow_redirects=True)
        f.write(r.content)

    return path


def _import_class(
    cid: str,
) -> type:
    # parse the class identifier
    if ":" not in cid:
        raise ValueError(f"invalid format, cannot import '{cid}'")
    module_name, cls_name = cid.split(":", 1)

    # import the module
    mod = importlib.import_module(module_name)

    # get the cls
    cls = getattr(mod, cls_name, None)
    if not cls:
        raise AttributeError(f"not class named '{cls_name}' in module {mod}")

    return cls


def main(
    cli_args: list[str] | None = None,
    test: bool = False,
) -> None | list[str] | str:
    """
    TODO.
    """
    import subprocess
    import tempfile
    import shlex
    import argparse

    # setup arguments
    parser = argparse.ArgumentParser(
        description="visualize class inheritance structures with mermaidjs using the mro",
        prog="mermaidmro",
    )
    parser.add_argument(
        "cls",
        help="the root class to visualize in the format 'module.to.import:class'",
    )
    parser.add_argument(
        "--max-depth",
        "-m",
        metavar="VALUE",
        help="the maximum depth of the graph; default: -1",
        type=int,
        default=-1,
    )
    parser.add_argument(
        "--cmd",
        "-c",
        metavar="CMD",
        help="an executable to open the generated url",
    )
    parser.add_argument(
        "--edit",
        "-e",
        action="store_true",
        help="whether to open the mermaid live editor instead of a static image when --cmd is set",
    )
    parser.add_argument(
        "--download",
        "-d",
        metavar="PATH",
        help="path for downloading the graph file instead",
    )
    parser.add_argument(
        "--visualize",
        "-v",
        metavar="CMD",
        help="executable for visualizing the graph from the (temporarily) downloaded file",
    )
    parser.add_argument(
        "--file-type",
        "-f",
        metavar="TYPE",
        help="the file type to open or download; has no effect when --edit is set",
        choices=["png", "jpg"],
        default="png",
    )
    parser.add_argument(
        "--args",
        "-a",
        help="additional arguments to be added to the commands given via --cmd or --visualize",
        type=shlex.split,
    )
    args = parser.parse_args(cli_args)

    # import the class
    cls = _import_class(args.cls)

    # generate the mermaid text
    mermaid_text = get_mermaid_text(
        cls,
        max_depth=args.max_depth,
    )

    # trigger actions
    show_text = True

    # download and / or visualize
    if args.download or args.visualize:
        with tempfile.NamedTemporaryFile(suffix=f".{args.file_type}") as f:
            vis_path = download_graph(
                mermaid_text,
                args.download or f.name,
                file_type=args.file_type,
            )

            if args.visualize:
                cmd = [args.visualize, vis_path] + (args.args or [])
                if test:
                    return cmd
                subprocess.run(cmd)

        show_text = False

    if args.cmd:
        # open an url
        if args.edit:
            url = URL_EDIT_JSON.format(encode_json(mermaid_text))
        else:
            url = URL_STATIC_JSON.format(encode_json(mermaid_text), args.file_type)

        # run the command
        cmd = [args.cmd, url] + (args.args or [])
        if test:
            return cmd
        subprocess.run(cmd)

        show_text = False

    if show_text:
        # just print the text
        if test:
            return mermaid_text
        print(mermaid_text)


# entry hook
if __name__ == "__main__":
    main()
