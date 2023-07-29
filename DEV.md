=== Development commands

Run tests with coverage:

```bash
> coverage run -m pytest -s && coverage report -m 
```

Check code with mypy and flake

```bash
> mypy jsno
> flake8
```

Build and publish:

```bash
> python -m build                                 
> twine upload -r pypi dist/*
```

Run performance benchmarks:

```bash

> python -m performance.measure_jsonify


```
