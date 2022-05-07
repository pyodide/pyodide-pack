def match_suffix(file_paths: list[str], suffix: str) -> str | None:
    """Match suffix in a list of file paths.

    Return the most likely path or None of None matched

    Examples
    --------
    >>> match_suffix(['/usr/a.py', '/usr/b/d.py'], 'd.py')
    '/usr/b/d.py'
    >>> match_suffix(['/usr/a.py', '/usr/b/d.py'], 'c.py')
    >>> match_suffix(['/usr/a.py', '/usr/b/a.py'], 'a.py')
    '/usr/a.py'
    """
    results = [el for el in file_paths if el.endswith(suffix)]
    match results:
        case []:
            return None
        case [path]:
            return path
        case _:
            # If there are multiple matches, we return the shortest
            # one as less likely to be a vendored package.
            # for instance numpy/__init__.py will match both
            #  - /lib/.../numpy/__init__.py
            #  - /lib/.../pandas/compat/numpy/__init__.py
            # however only the first one is correct
            results = list(sorted(results, key=len))
            return results[0]
