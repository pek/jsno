DEV.md

Run tests with coverage:

```bash
> coverage run -m pytest -s && coverage report -m 
```

Build and publish:

```bash
> python -m build                                 
> twine upload -r pypi dist/*
```

Run performance benchmarks:

```bash

> python -m performance.measure_jsonify

