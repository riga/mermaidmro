# mermaidmro

<!-- marker-before-badges -->

[![Build status](https://github.com/riga/mermaidmro/actions/workflows/lint_and_test.yml/badge.svg)](https://github.com/riga/mermaidmro/actions/workflows/lint_and_test.yml)
[![Package version](https://img.shields.io/pypi/v/mermaidmro.svg?style=flat)](https://pypi.python.org/pypi/mermaidmro)
[![Documentation status](https://readthedocs.org/projects/mermaidmro/badge/?version=latest)](http://mermaidmro.readthedocs.io)
[![Code coverge](https://codecov.io/gh/riga/mermaidmro/graph/badge.svg?token=UAKGC13BVI)](https://codecov.io/gh/riga/mermaidmro)
[![License](https://img.shields.io/github/license/riga/mermaidmro.svg)](https://github.com/riga/mermaidmro/blob/master/LICENSE)

<!-- marker-after-badges -->

Create mermaid graphs from the method resolution order (mro) of Python objects.


<!-- marker-before-content -->

## CLI Examples

For the examples below, let's consider the following classes saved in a file `code.py` that can be imported via `import code` (adjust your `PYTHONPATH` if this is not the case).

```python
class A(object):
    pass

class B(object):
    pass

class C(A):
    pass

class D(A, B):
    pass
```

### Generate mermaid text

Simply pass the module and class in the format `module_name:class_name` to `mermaidmro`.

```shell
> mermaidmro code:D

graph TD
    code.A --> code.D
    code.B --> code.D
    object --> code.A
    object --> code.B
```

You can limit the maximum depth via `--max-depth / -m`.

```shell
> mermaidmro code:D --max-depth 1

graph TD
    code.A --> code.D
    code.B --> code.D
```


### Open the graph in your browser

Just configure the executable of your browser you like to open the graph with via `--cmd / -c` (on Macs this is usually just `open`).
This functionality is based on the [mermaid.live](https://mermaid.live) service.

```shell
> mermaidmro code:D --cmd open

# opens https://mermaid.ink/img/pako:eNqrVkrOT0lVslJQSi9KLMhQCHGJyVMAApConqOCrq4dhIks7IQhnJ-UlZpcghB2xC7spKSjoJSbWpSbmJkCsrI6RqkkIzU3NQbIiVFKSU1LLM0piVGqVaoFANe4LEk=?type=png
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
