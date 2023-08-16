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

class D(A, B): pass  # noqa


# string representation of the test classes
test_code = """
class A(object): pass
class B(object): pass
class C(A): pass
class D(A, B): pass
"""


class TestCore(unittest.TestCase):

    def test_get_relations(self):
        all_relations = (
            ("<class 'tests.test_all.D'>", "<class 'tests.test_all.A'>", "1"),
            ("<class 'tests.test_all.D'>", "<class 'tests.test_all.B'>", "1"),
            ("<class 'tests.test_all.A'>", "<class 'object'>", "2"),
            ("<class 'tests.test_all.B'>", "<class 'object'>", "2"),
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
    tests.test_all.A --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D
    object --> tests.test_all.A
    object --> tests.test_all.B""",
        )

        # unjoined lines
        self.assertEqual(
            tuple(mm.get_mermaid_text(D, join_lines=False)),
            (
                "graph TD",
                "    tests.test_all.A --> tests.test_all.D",
                "    tests.test_all.B --> tests.test_all.D",
                "    object --> tests.test_all.A",
                "    object --> tests.test_all.B",
            ),
        )

        # changed indentation
        self.assertEqual(
            mm.get_mermaid_text(D, indentation="  "),
            """graph TD
  tests.test_all.A --> tests.test_all.D
  tests.test_all.B --> tests.test_all.D
  object --> tests.test_all.A
  object --> tests.test_all.B""",
        )

        # limited depth
        self.assertEqual(
            mm.get_mermaid_text(D, max_depth=1),
            """graph TD
    tests.test_all.A --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D""",
        )

        # changed graph type
        self.assertEqual(
            mm.get_mermaid_text(D, graph_type="LR", join_lines=False)[0],
            "graph LR",
        )

        # changed arrow type
        self.assertEqual(
            mm.get_mermaid_text(D, arrow_type="--->"),
            """graph TD
    tests.test_all.A ---> tests.test_all.D
    tests.test_all.B ---> tests.test_all.D
    object ---> tests.test_all.A
    object ---> tests.test_all.B""",
        )

        # custom name func
        self.assertEqual(
            mm.get_mermaid_text(D, skip_modules=["tests.test_all"]),
            """graph TD
    A --> D
    B --> D
    object --> A
    object --> B""",
        )
        self.assertEqual(
            mm.get_mermaid_text(D, skip_modules=["tests.*"]),
            """graph TD
    A --> D
    B --> D
    object --> A
    object --> B""",
        )

        # include styles
        self.assertEqual(
            mm.get_mermaid_text(D, styles=[("Foo", "tests.test_all.D", "stroke: #83b")]),
            """graph TD
    tests.test_all.A --> tests.test_all.D
    tests.test_all.B --> tests.test_all.D
    object --> tests.test_all.A
    object --> tests.test_all.B

    classDef Foo stroke: #83b

    class tests.test_all.D Foo""",
        )

    def test_encode_text(self):
        self.assertEqual(
            mm.encode_text(mm.get_mermaid_text(D)),
            "Z3JhcGggVEQKICAgIHRlc3RzLnRlc3RfYWxsLkEgLS0-IHRlc3RzLnRlc3RfYWxsLkQKICAgIHRlc3RzLnRlc3RfYWxsLkIgLS0-IHRlc3RzLnRlc3RfYWxsLkQKICAgIG9iamVjdCAtLT4gdGVzdHMudGVzdF9hbGwuQQogICAgb2JqZWN0IC0tPiB0ZXN0cy50ZXN0X2FsbC5C",  # noqa
        )

    def test_encode_json(self):
        self.assertEqual(
            mm.encode_json(mm.get_mermaid_text(D)),
            "eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgpLU4pJiPRAZn5iTo-eooKtrhy6IXakTHqX5SVmpySXYFDgSUuCkpKOglJtalJuYmQJybnWMUklGam5qDJATo5SSmpZYmlMSo1SrVAsAknRE_Q==",  # noqa
        )
        self.assertEqual(
            mm.encode_json(mm.get_mermaid_text(D), theme="dark"),
            "eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgpLU4pJiPRAZn5iTo-eooKtrhy6IXakTHqX5SVmpySXYFDgSUuCkpKOglJtalJuYmQJybnWMUklGam5qDJATo5SSWJQdo1SrVAsAw1dDug==",  # noqa
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
    mm_test_module.A --> mm_test_module.D
    mm_test_module.B --> mm_test_module.D
    object --> mm_test_module.A
    object --> mm_test_module.B""",
            )

            # limited depth
            self.assertEqual(
                self.main(["mm_test_module:D", "-m", "1"]),
                """graph TD
    mm_test_module.A --> mm_test_module.D
    mm_test_module.B --> mm_test_module.D""",
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
                "open https://mermaid.ink/img/pako:eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgtzc-JLU4pL43PyU0pxUPUcFXV07dEHsSp3wKM1PykpNLsGmwJGQAiclHQWl3NSi3MTMFJBzq2OUSjJSc1NjgJwYpZTUtMTSnJIYpVqlWgD6QUXb?type=png",  # noqa
            )

            # jpg
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open", "-f", "jpg"])),
                "open https://mermaid.ink/img/pako:eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgtzc-JLU4pL43PyU0pxUPUcFXV07dEHsSp3wKM1PykpNLsGmwJGQAiclHQWl3NSi3MTMFJBzq2OUSjJSc1NjgJwYpZTUtMTSnJIYpVqlWgD6QUXb?type=jpg",  # noqa
            )

            # edit page
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open", "-e"])),
                "open https://mermaid.live/edit#pako:eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgtzc-JLU4pL43PyU0pxUPUcFXV07dEHsSp3wKM1PykpNLsGmwJGQAiclHQWl3NSi3MTMFJBzq2OUSjJSc1NjgJwYpZTUtMTSnJIYpVqlWgD6QUXb",  # noqa
            )

            # additional args
            self.assertEqual(
                " ".join(self.main(["mm_test_module:D", "-c", "open", "-a", "foo bar"])),
                "open https://mermaid.ink/img/pako:eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAgtzc-JLU4pL43PyU0pxUPUcFXV07dEHsSp3wKM1PykpNLsGmwJGQAiclHQWl3NSi3MTMFJBzq2OUSjJSc1NjgJwYpZTUtMTSnJIYpVqlWgD6QUXb?type=png foo bar",  # noqa
            )
