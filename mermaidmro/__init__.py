# coding: utf-8

from __future__ import annotations

__all__ = [
    "get_mermaid_text",
    "get_style_text",
    "get_relations",
    "encode_text",
    "encode_json",
    "download_graph",
    "get_default_name_func",
]

import os
import zlib
import base64
import json
import importlib
import fnmatch
import collections
import urllib.request
from typing import Callable

try:
    import requests
    HAS_REQUESTS = True
except ModuleNotFoundError:
    HAS_REQUESTS = False

# package infos
from mermaidmro.__meta__ import (  # noqa
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

#: Relation between two classes including a depth value and the mro index with respect to the
#: requested root class (namedtuple).
Relation = collections.namedtuple("Relation", ["cls", "base_cls", "root_cls", "depth", "mro"])

#: Container object with attributes to define css styles for one or multiple classes (namedtuple).
Style = collections.namedtuple("Style", ["name", "cls", "css"])


def get_relations(
    root_cls: type,
    max_depth: int = -1,
) -> list[Relation]:
    """
    Recursively extracts base classes of a *root_cls* down to a maximum depth *max_depth* and
    returns them in a list of :py:class:`Relation` objects. When *max_depth* is negative, the lookup
    is fully recursive, possibly down to ``object``.

    :param root_cls: The root class to use.
    :param max_depth: Maximum recursion depth.
    :return: The list of found :py:class:`Relation` objects.
    """
    # stop early
    if max_depth == 0:
        return []

    # get the mro
    mro = {cls: i for i, cls in enumerate(root_cls.__mro__)}

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
            relations.append(Relation(cls, base_cls, root_cls, depth + 1, mro.get(base_cls, -1)))

            # ammend lookup when depth below maximum
            if max_depth < 0 or depth + 1 < max_depth:
                lookup.append((base_cls, depth + 1))

        # mark as seen
        seen.add(cls)

    return relations


def get_default_name_func(
    skip_modules: list[str] | set[str] | None = None,
) -> Callable[[type], str]:
    """
    Returns a function that takes an arbitrary class and extracts its name representation, usually
    in the format ``"module_name.class_name"``. *skip_modules* can be a sequence of modules names
    of patterns matching module names that are not preprended. Please note that ``builtins`` and
    ``__main__`` are always skipped.

    :param skip_modules: Optional squence of module names (or patterns) to skip.
    :return: Function that takes a class and returns the name for visualization.
    """
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
    Creates the string representation of style statements for mermaid graphs consisting of style
    definitions followed by assignments to graph nodes. *styles* should be a sequence of
    :py:class:`Style` objects (or tuples that can be interpreted as such) containing the name of the
    style, the name(s) of the class(es) it is applied to, and one or multiple css-like strings, e.g.
    ``"stroke-width: 3px"``. Example:

    .. code-block:: python

        get_style_text([
            Style(name="Bold", cls=["ClassA", "ClassB"], css=["stroke-width: 3px"]),
            Style(name="Colored", cls="ClassA", css=["stroke-width: 3px", "stroke: #83b"]),
        ])

        #    classDef Bold stroke-width: 3px
        #    classDef Colored stroke-width: 3px, stroke: #83b
        #
        #    class ClassA Bold
        #    class ClassB Bold
        #    class ClassA Colored

    :param styles: Sequence of :py:class:`Style` objects or tuples that can be interpreted as such.
    :param indentation: The indentation of lines.
    :param name_func: A function to extract the string representation of a class, defaulting to the
        return value of :py:func:`get_default_name_func` passing *skip_modules*.
    :param skip_modules: Sequence of module names (or patterns) to skip when no *name_func* is set.
    :param join_lines: Whether generated lines should be joined to a string.
    :return: The style as a text representation or as single lines in a list.
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
            style.css
            if isinstance(style.css, str)
            else ", ".join(style.css)
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
    styles: list[Style | tuple] | None = None,
    show_mro: bool = True,
    graph_type: str = "TD",
    arrow_type: str = "-->",
    indentation: str = "    ",
    skip_func: Callable[[type, Callable], bool] | None = None,
    name_func: Callable[[type], str] | None = None,
    skip_modules: list[str] | set[str] | None = None,
    join_lines: bool = True,
) -> str | list[str]:
    """
    Creates a text representation of the inheritance graph for a *root_cls*, down to a maximum
    recursion depth *max_depth*. When *styles* is given, the representation contains style
    statements generated via :py:func:`get_style_text`. When *show_mro* is *True*, mro indices with
    respect to *root_cls* are shown. The type of the graph and style of arrows can be controlled
    with *graph_type* and *arrow_type*. Example:

    .. code-block:: python

        class A(object): pass
        class B(object): pass
        class C(A): pass
        class D(C, B): pass

        get_mermaid_text(D)
        # graph TD
        #     D("D (0)")
        #     C("C (1)")
        #     A("A (2)")
        #     B("B (3)")
        #     object("object (4)")
        #
        #     C --> D
        #     B --> D
        #     A --> C
        #     object --> A
        #     object --> B

        get_mermaid_text(D, show_mro=False)
        # graph TD
        #     C --> D
        #     B --> D
        #     A --> C
        #     object --> A
        #     object --> B

    :param root_cls: The root class to use.
    :param max_depth: Maximum recursion depth for the lookup in :py:func:`get_relations`.
    :param styles: Sequence of :py:class:`Style` objects or tuples that can be interpreted as such.
    :param show_mro: Whether mro indices should be included.
    :param graph_type: The mermaid graph type to use, e.g. ``"TD"`` or ``"LR"``.
    :param arrow_type: The default arrow type to use between classes, e.g. ``"-->"``.
    :param indentation: The indentation of lines.
    :param skip_func: A function to decide whether a specific base class should be skipped given
        the class itself and the *name_func* as arguments.
    :param name_func: A function to extract the string representation of a class, defaulting to the
        return value of :py:func:`get_default_name_func` passing *skip_modules*.
    :param skip_modules: Sequence of module names (or patterns) to skip when no *name_func* is set.
    :param join_lines: Whether generated lines should be joined to a string.
    :return: The style as a text representation or as single lines in a list.
    """
    # default name_func
    if name_func is None:
        name_func = get_default_name_func(skip_modules=skip_modules)

    # get relations
    relations = get_relations(root_cls, max_depth=max_depth)

    # build lines
    lines = [f"graph {graph_type}"]

    # add labels with mro indices
    if show_mro:
        mro_label = lambda cls, i: f"{indentation}{name_func(cls)}(\"{name_func(cls)} ({i})\")"
        mro_pairs = {(root_cls, 0)} | {(rel.base_cls, rel.mro) for rel in relations}
        lines.extend([
            mro_label(base_cls, mro)
            for base_cls, mro in sorted(mro_pairs, key=lambda tpl: tpl[1])
        ])
        lines.append("")

    # add relations
    for rel in relations:
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
    Returns a base64 encoded variant of a mermaid graph given in *mermaid_text*, that is usually
    used in static urls of the mermaidjs service.

    :param mermaid_text: The graph as a string representation.
    :return: The base64 encoded representation of the text.
    """
    return base64.urlsafe_b64encode(mermaid_text.encode("utf-8")).decode("utf-8")


def encode_json(
    mermaid_text: str,
    theme: str | None = "default",
) -> str:
    r"""
    Returns a base64 encoded and compressed variant of a mermaid graph given in *mermaid_text* and
    additional configuration options such as *theme*, that is usually used in urls of the mermaidjs
    live editing service.

    The structured data that is compressed has the format

    .. code-block:: json

        {
            "code": "graph TD\n....",
            "mermaid": "{\"theme\": ...}"
        }

    as expected by mermaidjs.

    :param mermaid_text: The graph as a string representation.
    :param theme: Name of the theme to use.
    :return: The base64 encoded and compressed representation of the structured data containing
        the graph and configuration options.
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
    theme: str | None = "default",
) -> str:
    """
    Downloads a mermaid graph represented by *mermaid_text* from the mermaidjs service to a *path*
    in a specific *file_type*. Missing intermediate directories are created first.

    :param mermaid_text: The graph as a string representation.
    :param path: The path where the downloaded file should be saved.
    :param file_type: The file type to write, usually ``"jpg"`` or ``"png"``.
    :param theme: Name of the theme to use.
    :return: The absolute, normalized and expanded path.
    """
    # normalize path
    path = os.path.normpath(os.path.expandvars(os.path.expanduser(path)))

    # ensure parent directory exists
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)

    # download and write
    url = URL_STATIC_JSON.format(encode_json(mermaid_text, theme=theme), file_type)
    if HAS_REQUESTS:
        with open(path, "wb") as f:
            r = requests.get(url, allow_redirects=True)
            f.write(r.content)
    else:
        opener = urllib.request.build_opener()
        opener.addheaders = [("User-Agent", f"mermaidmro/{__version__}")]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, path)

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
    Main entry hook of the mermaidmro cli.

    The arguments to parse can be configured via *cli_args* and default to ``sys.argv[1:]``. When
    *test* is *True*, no command is executed by created texts and / or commands are returned instead
    for testing purposes.

    :param cli_args: Custom cli arguments.
    :param test: Whether texts and or commands are returned for testing purposes.
    :return: Texts or commands if *test* is *True* and *None* otherwise.
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
        "--no-mro",
        "-n",
        action="store_true",
        help="do not show mro indices",
    )
    parser.add_argument(
        "--graph-type",
        "-g",
        help="the graph type; default: 'TD'",
        default="TD",
    )
    parser.add_argument(
        "--arrow-type",
        "-a",
        help="the arrow type; default: '-->'",
        default="-->",
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
        help="additional arguments to be added to the commands given via --cmd or --visualize",
        type=shlex.split,
    )
    args = parser.parse_args(cli_args)

    # overwrite the file type when downloading
    if args.download:
        args.file_type = os.path.splitext(args.download)[-1].strip(".") or args.file_type

    # import the class
    cls = _import_class(args.cls)

    # generate the mermaid text
    mermaid_text = get_mermaid_text(
        cls,
        max_depth=args.max_depth,
        show_mro=not args.no_mro,
        graph_type=args.graph_type.strip(),
        arrow_type=args.arrow_type.strip(),
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
        mermaid_json = encode_json(mermaid_text)
        if args.edit:
            url = URL_EDIT_JSON.format(mermaid_json)
        else:
            url = URL_STATIC_JSON.format(mermaid_json, args.file_type)

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
