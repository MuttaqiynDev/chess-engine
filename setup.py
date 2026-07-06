from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(
        ["engine/evaluate.pyx", "engine/ordering.pyx", "engine/quiescence.pyx", "engine/search.pyx"],
        compiler_directives={'language_level': "3"}
    )
)
