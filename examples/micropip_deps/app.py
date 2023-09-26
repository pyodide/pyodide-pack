# Examples of a package that is installed by micropip from PyPI

import snowballstemmer

stemmer = snowballstemmer.stemmer("english")
print(stemmer.stemWords("An example of stemming".split()))
