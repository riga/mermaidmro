# coding: utf-8


__all__ = ["TestCore", "TestCLI"]


import os
import sys
import tempfile
import contextlib
import functools
import fnmatch
import unittest

import mermaidmro as mm

try:
    import requests  # noqa
    HAS_REQUESTS = True
except ModuleNotFoundError:
    HAS_REQUESTS = False


# test classes
class A(object): pass  # noqa

class B(object): pass  # noqa

class C(A): pass  # noqa

class D(C, B): pass  # noqa


# string representation of the test classes
test_code = """
class A(object): pass
class B(object): pass
class C(A): pass
class D(C, B): pass
"""


class TestCore(unittest.TestCase):

    def test_get_relations(self):
        root_cls = "<class 'tests.test_all.D'>"
        all_relations = (
            ("<class 'tests.test_all.D'>", "<class 'tests.test_all.C'>", root_cls, "1", "1"),
            ("<class 'tests.test_all.D'>", "<class 'tests.test_all.B'>", root_cls, "1", "3"),
            ("<class 'tests.test_all.C'>", "<class 'tests.test_all.A'>", root_cls, "2", "2"),
            ("<class 'tests.test_all.B'>", "<class 'object'>", root_cls, "2", "4"),
            ("<class 'tests.test_all.A'>", "<class 'object'>", root_cls, "3", "4"),
        )

        # full depth
        self.assertEqual(
            tuple(map((lambda r: tuple(map(str, r))), mm.get_relations(D))),
            all_relations,
        )

        # limited depth
        self.assertEqual(
            tuple(map((lambda r: tuple(map(str, r))), mm.get_relations(D, max_depth=1))),
            all_relations[:2],
        )

    def test_get_default_name_func(self):
        # default skip modules
        name_func = mm.get_default_name_func()
        self.assertEqual(name_func(object), "object")
        self.assertEqual(name_func(D), "tests.test_all.D")

        # ammended skip modules
        name_func = mm.get_default_name_func(["tests.test_all"])
        self.assertEqual(name_func(object), "object")
        self.assertEqual(name_func(D), "D")

    def test_get_style_text(self):
        # default case
        self.assertEqual(
            mm.get_style_text([("Foo", "X", "stroke: #83b")]),
            "    classDef Foo stroke: #83b\n\n    class X Foo",
        )

        # unjoined lines
        self.assertEqual(
            tuple(mm.get_style_text([("Foo", "X", "stroke: #83b")], join_lines=False)),
            ("    classDef Foo stroke: #83b", "", "    class X Foo"),
        )

        # changed indentation
        self.assertEqual(
            mm.get_style_text([("Foo", "X", "stroke: #83b")], indentation="  "),
            "  classDef Foo stroke: #83b\n\n  class X Foo",
        )

        # multiple classes
        self.assertEqual(
            mm.get_style_text([("Foo", ["X", "Y"], "stroke: #83b")]),
            "    classDef Foo stroke: #83b\n\n    class X Foo\n    class Y Foo",
        )

        # multiple styles
        self.assertEqual(
            mm.get_style_text([("Foo", "X", ["stroke: #83b", "stroke-width: 3px"])]),
            "    classDef Foo stroke: #83b, stroke-width: 3px\n\n    class X Foo",
        )

        # multiple classes and styles
        self.assertEqual(
            mm.get_style_text([("Foo", ["X", "Y"], ["stroke: #83b", "stroke-width: 3px"])]),
            "    classDef Foo stroke: #83b, stroke-width: 3px\n\n    class X Foo\n    class Y Foo",
        )

        # using Style objects
        self.assertEqual(
            mm.get_style_text([mm.Style("Foo", ["X", "Y"], ["stroke: #83b", "stroke-width: 3px"])]),
            "    classDef Foo stroke: #83b, stroke-width: 3px\n\n    class X Foo\n    class Y Foo",
        )

    def test_get_mermaid_text(self):
        # default case
        self.assertEqual(
            mm.get_mermaid_text(D),
            """graph TD
    tests.test_all.D("tests.test_all.D (0)")
    tests.test_all.C("tests.test_all.C (1)")
    tests.test_all.A("tests.test_all.A (2)")
    tests.test_all.B("tests.test_all.B (3)")
    object("object (4)")

    tests.test_all.C --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D
    tests.test_all.A --> tests.test_all.C
    object --> tests.test_all.B
    object --> tests.test_all.A""",
        )

        # hidden mro from now onwards
        get_mermaid_text = functools.partial(mm.get_mermaid_text, show_mro=False)
        self.assertEqual(
            get_mermaid_text(D),
            """graph TD
    tests.test_all.C --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D
    tests.test_all.A --> tests.test_all.C
    object --> tests.test_all.B
    object --> tests.test_all.A""",
        )

        # unjoined lines
        self.assertEqual(
            tuple(get_mermaid_text(D, join_lines=False)),
            (
                "graph TD",
                "    tests.test_all.C --> tests.test_all.D",
                "    tests.test_all.B --> tests.test_all.D",
                "    tests.test_all.A --> tests.test_all.C",
                "    object --> tests.test_all.B",
                "    object --> tests.test_all.A",
            ),
        )

        # changed indentation
        self.assertEqual(
            get_mermaid_text(D, indentation="  "),
            """graph TD
  tests.test_all.C --> tests.test_all.D
  tests.test_all.B --> tests.test_all.D
  tests.test_all.A --> tests.test_all.C
  object --> tests.test_all.B
  object --> tests.test_all.A""",
        )

        # limited depth
        self.assertEqual(
            get_mermaid_text(D, max_depth=1),
            """graph TD
    tests.test_all.C --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D""",
        )

        # changed graph type
        self.assertEqual(
            get_mermaid_text(D, graph_type="LR", join_lines=False)[0],
            "graph LR",
        )

        # changed arrow type
        self.assertEqual(
            get_mermaid_text(D, arrow_type="--->"),
            """graph TD
    tests.test_all.C ---> tests.test_all.D
    tests.test_all.B ---> tests.test_all.D
    tests.test_all.A ---> tests.test_all.C
    object ---> tests.test_all.B
    object ---> tests.test_all.A""",
        )

        # custom name func
        self.assertEqual(
            get_mermaid_text(D, skip_modules=["tests.test_all"]),
            """graph TD
    C --> D
    B --> D
    A --> C
    object --> B
    object --> A""",
        )
        self.assertEqual(
            get_mermaid_text(D, skip_modules=["tests.*"]),
            """graph TD
    C --> D
    B --> D
    A --> C
    object --> B
    object --> A""",
        )

        # skip func
        self.assertEqual(
            get_mermaid_text(D, skip_func=(lambda cls, name_func: cls == B)),
            """graph TD
    tests.test_all.C --> tests.test_all.D
    tests.test_all.A --> tests.test_all.C
    object --> tests.test_all.B
    object --> tests.test_all.A""",
        )

        # include styles
        self.assertEqual(
            get_mermaid_text(D, styles=[("Foo", "tests.test_all.D", "stroke: #83b")]),
            """graph TD
    tests.test_all.C --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D
    tests.test_all.A --> tests.test_all.C
    object --> tests.test_all.B
    object --> tests.test_all.A

    classDef Foo stroke: #83b

    class tests.test_all.D Foo""",
        )

    def test_encode_text(self):
        self.assertEqual(
            mm.encode_text(mm.get_mermaid_text(D)),
            "Z3JhcGggVEQKICAgIHRlc3RzLnRlc3RfYWxsLkQoInRlc3RzLnRlc3RfYWxsLkQgKDApIikKICAgIHRlc3RzLnRlc3RfYWxsLkMoInRlc3RzLnRlc3RfYWxsLkMgKDEpIikKICAgIHRlc3RzLnRlc3RfYWxsLkEoInRlc3RzLnRlc3RfYWxsLkEgKDIpIikKICAgIHRlc3RzLnRlc3RfYWxsLkIoInRlc3RzLnRlc3RfYWxsLkIgKDMpIikKICAgIG9iamVjdCgib2JqZWN0ICg0KSIpCgogICAgdGVzdHMudGVzdF9hbGwuQyAtLT4gdGVzdHMudGVzdF9hbGwuRAogICAgdGVzdHMudGVzdF9hbGwuQiAtLT4gdGVzdHMudGVzdF9hbGwuRAogICAgdGVzdHMudGVzdF9hbGwuQSAtLT4gdGVzdHMudGVzdF9hbGwuQwogICAgb2JqZWN0IC0tPiB0ZXN0cy50ZXN0X2FsbC5CCiAgICBvYmplY3QgLS0-IHRlc3RzLnRlc3RfYWxsLkE=",  # noqa
        )
        self.assertEqual(
            mm.encode_text(mm.get_mermaid_text(D, show_mro=False)),
            "Z3JhcGggVEQKICAgIHRlc3RzLnRlc3RfYWxsLkMgLS0-IHRlc3RzLnRlc3RfYWxsLkQKICAgIHRlc3RzLnRlc3RfYWxsLkIgLS0-IHRlc3RzLnRlc3RfYWxsLkQKICAgIHRlc3RzLnRlc3RfYWxsLkEgLS0-IHRlc3RzLnRlc3RfYWxsLkMKICAgIG9iamVjdCAtLT4gdGVzdHMudGVzdF9hbGwuQgogICAgb2JqZWN0IC0tPiB0ZXN0cy50ZXN0X2FsbC5B",  # noqa
        )

    def test_encode_json(self):
        self.assertEqual(
            mm.encode_json(mm.get_mermaid_text(D)),
            "eNqN0c0OwiAMAOBXaXpiiVv8O3kwAfYIHkkMjuo04MyGp2XvLssOGmHRHgiFL2mhPVaNIdwBXlr9qOFQqjuE8NT5rhjXo7a2KJnC7yNgy0xhlvQy9hLYatbz2HNg61kvYi-Abd6-Od2o8kFNG2Db6S7dLeT5PnpyuvD_lKeo_GwvBcQvwHEB6Kh1-mrGufXhJ2pypEKi0NBZP61XOODwAp_3mpk=",  # noqa
        )
        self.assertEqual(
            mm.encode_json(mm.get_mermaid_text(D), theme="dark"),
            "eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgpLU4pJiPRAZn5iTo-eiEaOELqSgYaAZo6SJVb0zpnpnBQ1DnOodMdU7KmgY4VTvhKneSUHDGKE-PykrNbkEqArCUNAwgchhd62Crq4dhpexW0y8UkdsSp2RnYdNgRMhBY5KOgpKualFuYmZKaB4qwaGREZqbmoMkBOjlJJYlB2jVKtUCwDP95lW",  # noqa
        )

    def test_download_graph(self):
        if not HAS_REQUESTS:
            return

        for ext in ["png", "jpg"]:
            with tempfile.NamedTemporaryFile(suffix=f".{ext}") as f:
                if os.path.exists(f.name):
                    os.remove(f.name)
                mm.download_graph(mm.get_mermaid_text(D), f.name, file_type=ext)
                self.assertTrue(os.path.exists(f.name))

    def test_import_class(self):
        with tempfile.TemporaryDirectory() as d:
            module_dir = os.path.join(d, "mermaidmro_test_dir")
            os.makedirs(module_dir)
            sys.path.insert(0, module_dir)

            with open(os.path.join(module_dir, "mm_test_module.py"), "w") as f:
                f.write(test_code)

            with self.assertRaises(ValueError):
                mm._import_class("mm_test_module")

            with self.assertRaises(AttributeError):
                mm._import_class("mm_test_module:NotExisting")

            cls = mm._import_class("mm_test_module:D")
            self.assertEqual(str(cls), "<class 'mm_test_module.D'>")


class TestCLI(unittest.TestCase):

    @classmethod
    @contextlib.contextmanager
    def build_module(cls):
        with tempfile.TemporaryDirectory() as d:
            module_dir = os.path.join(d, "mermaidmro_test_dir")
            os.makedirs(module_dir)
            sys.path.insert(0, module_dir)

            with open(os.path.join(module_dir, "mm_test_module.py"), "w") as f:
                f.write(test_code)

            yield

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main = functools.partial(mm.main, test=True)

    def test_show_mermaid_text(self):
        with self.build_module():
            # default case
            self.assertEqual(
                self.main(["mm_test_module:D"]),
                """graph TD
    mm_test_module.D("mm_test_module.D (0)")
    mm_test_module.C("mm_test_module.C (1)")
    mm_test_module.A("mm_test_module.A (2)")
    mm_test_module.B("mm_test_module.B (3)")
    object("object (4)")

    mm_test_module.C --> mm_test_module.D
    mm_test_module.B --> mm_test_module.D
    mm_test_module.A --> mm_test_module.C
    object --> mm_test_module.B
    object --> mm_test_module.A""",
            )

            # hidden mro indices
            self.assertEqual(
                self.main(["mm_test_module:D", "-n"]),
                """graph TD
    mm_test_module.C --> mm_test_module.D
    mm_test_module.B --> mm_test_module.D
    mm_test_module.A --> mm_test_module.C
    object --> mm_test_module.B
    object --> mm_test_module.A""",
            )

            # changed graph and arrow type
            self.assertEqual(
                self.main(["mm_test_module:D", "-n", "-g", "LR", "-a", " --->"]),
                """graph LR
    mm_test_module.C ---> mm_test_module.D
    mm_test_module.B ---> mm_test_module.D
    mm_test_module.A ---> mm_test_module.C
    object ---> mm_test_module.B
    object ---> mm_test_module.A""",
            )

    def test_visualize(self):
        with self.build_module():
            # default case
            self.assertTrue(fnmatch.fnmatch(
                " ".join(self.main(["mm_test_module:D", "-v", "imgcat"])),
                "imgcat /*.png",
            ))

            # download case
            with tempfile.NamedTemporaryFile(suffix=".png") as f:
                self.assertEqual(
                    " ".join(self.main(["mm_test_module:D", "-v", "imgcat", "-d", f.name])),
                    f"imgcat {f.name}",
                )

    def test_open_url(self):
        with self.build_module():
            # default case
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open"])),
                "open https://mermaid.ink/img/pako:eNqN0c0KwjAMAOBXCTl14MS_kweh7R7BY2DMNTplXWV2p7F3d7KDYjs0pzT5ICnpsXSGcQ94aYt7BceMGhjD2tzzw-fWma7mZSYIv0sgVglhEvU69BrEetbL0EsQm1mvQq9AbN_enW5c-lFNCYjd1ItvC2l6CL4cH_w_lTGqP9eLAfULSFwAWm5tcTWvu_WEvmLLND4IDZ-LrvaEAw5P5_ec6Q==?type=png",  # noqa
            )

            # jpg
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open", "-f", "jpg"])),
                "open https://mermaid.ink/img/pako:eNqN0c0KwjAMAOBXCTl14MS_kweh7R7BY2DMNTplXWV2p7F3d7KDYjs0pzT5ICnpsXSGcQ94aYt7BceMGhjD2tzzw-fWma7mZSYIv0sgVglhEvU69BrEetbL0EsQm1mvQq9AbN_enW5c-lFNCYjd1ItvC2l6CL4cH_w_lTGqP9eLAfULSFwAWm5tcTWvu_WEvmLLND4IDZ-LrvaEAw5P5_ec6Q==?type=jpg",  # noqa
            )

            # edit page
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open", "-e"])),
                "open https://mermaid.live/edit#pako:eNqN0c0KwjAMAOBXCTl14MS_kweh7R7BY2DMNTplXWV2p7F3d7KDYjs0pzT5ICnpsXSGcQ94aYt7BceMGhjD2tzzw-fWma7mZSYIv0sgVglhEvU69BrEetbL0EsQm1mvQq9AbN_enW5c-lFNCYjd1ItvC2l6CL4cH_w_lTGqP9eLAfULSFwAWm5tcTWvu_WEvmLLND4IDZ-LrvaEAw5P5_ec6Q==",  # noqa
            )

            # additional args
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open", "--args", "foo bar"])),
                "open https://mermaid.ink/img/pako:eNqN0c0KwjAMAOBXCTl14MS_kweh7R7BY2DMNTplXWV2p7F3d7KDYjs0pzT5ICnpsXSGcQ94aYt7BceMGhjD2tzzw-fWma7mZSYIv0sgVglhEvU69BrEetbL0EsQm1mvQq9AbN_enW5c-lFNCYjd1ItvC2l6CL4cH_w_lTGqP9eLAfULSFwAWm5tcTWvu_WEvmLLND4IDZ-LrvaEAw5P5_ec6Q==?type=png foo bar",  # noqa
            )
