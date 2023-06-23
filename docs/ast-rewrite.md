(=ast-rewrite)

# Abstract Syntax Tree (AST) Rewrite

In this section we apply Abstract Syntax Tree (AST) rewrites to the package source code. These include,

 - removal of comments
 - removal of function and class docstrings
 - removal of module docstrings

To apply rewrites on one or multiple wheels, run,
```bash
pyodide minify <path.whl>
```
