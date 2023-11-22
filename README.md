# mermaidmro

<!-- marker-before-badges -->

[![Build status](https://github.com/riga/mermaidmro/actions/workflows/lint_and_test.yml/badge.svg)](https://github.com/riga/mermaidmro/actions/workflows/lint_and_test.yml)
[![Package version](https://img.shields.io/pypi/v/mermaidmro.svg?style=flat)](https://pypi.python.org/pypi/mermaidmro)
[![Python version](https://img.shields.io/badge/Python-%E2%89%A53.7-blue)](https://pypi.python.org/pypi/mermaidmro)
[![Documentation status](https://readthedocs.org/projects/mermaidmro/badge/?version=latest)](http://mermaidmro.readthedocs.io)
[![Code coverge](https://codecov.io/gh/riga/mermaidmro/graph/badge.svg?token=UAKGC13BVI)](https://codecov.io/gh/riga/mermaidmro)
[![License](https://img.shields.io/github/license/riga/mermaidmro.svg)](https://github.com/riga/mermaidmro/blob/master/LICENSE)

<!-- marker-after-badges -->

Create mermaid graphs from the method resolution order (mro) of Python objects.


<!-- marker-before-content -->

## CLI Examples

For the examples below, let's consider the following classes saved in a file `code.py` that can be imported via `import code` (adjust your `PYTHONPATH` if this is not the case).

```python
# code.py

class A(object):
    pass

class B(object):
    pass

class C(A):
    pass

class D(C, B):
    pass
```

### Generate mermaid text

Simply pass the module and class in the format `module_name:class_name` to `mermaidmro`.

```shell
> mermaidmro code:D

graph TD
    code.D("code.D (0)")
    code.C("code.C (1)")
    code.A("code.A (2)")
    code.B("code.B (3)")
    object("object (4)")

    code.C --> code.D
    code.B --> code.D
    code.A --> code.C
    object --> code.B
    object --> code.A
```

You can hide the mro indices by adding `--no-mro / -n`.

```shell
> mermaidmro code:D --no-mro

graph TD
    code.C --> code.D
    code.B --> code.D
    code.A --> code.C
    object --> code.B
    object --> code.A
```

You can also limit the maximum depth via `--max-depth / -m`.

```shell
> mermaidmro code:D --no-mro --max-depth 1

graph TD
    code.A --> code.D
    code.B --> code.D
```


### Open the graph in your browser

Just configure the executable of your browser you like to open the graph with via `--cmd / -c` (on Macs this is usually just `open`).
This functionality is based on the [mermaid.live](https://mermaid.live) service.

```shell
> mermaidmro code:D --cmd open

# opens https://mermaid.ink/img/pako:eNptkM8KwjAMh18l5JSBE_-dPAht9wgec6lbdYrdZNTT2LvbUUvLWE6_fB8kISPWfWPwDPgY9KeFa8Ud-JrptiLGEIB2BWORORWdAtovnIhOAB0WTkYngY7J9beXqZ13IQCdgss3Qlle_oflA9exSFjlKxKW61jgBtCawepnM_9lZHStsYZ9w9iYu_6-HeOE0w_Nr1i5?type=png
```

To open the graph in the live editor, add `--edit`.


### Visualize the graph in your terminal

This requires that you have a tool installed that lets you visualize images in your terminal, e.g. [`imgcat`](https://iterm2.com/documentation-images.html) for [iTerm2](https://iterm2.com).

```shell
> mermaidmro code:D --visualize imgcat

# shows
```

![code:D graph](https://media.githubusercontent.com/media/riga/mermaidmro/master/assets/graph.png)


### Download the graph

```shell
> mermaidmro code:D --download graph.png
```


## Installation

Simply install via [pip](https://pypi.python.org/pypi/mermaidmro)

```bash
pip install mermaidmro
```


## Development

- Source hosted at [GitHub](https://github.com/riga/mermaidmro)
- Report issues, questions, feature requests on [GitHub Issues](https://github.com/riga/mermaidmro/issues)

If you like to contribute, I'm happy to receive pull requests.
Just make sure to add a new test cases and run linting and coverage checks:

```bash
> ./tests/test.sh
> ./tests/lint.sh
> ./tests/coverage.sh
```

<!-- marker-after-content -->
