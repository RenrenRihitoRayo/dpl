from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# Define the custom output path
output_dir = os.getcwd()

ext_modules = [Extension(name="parser", sources=["py_parser.py"])]

setup(
    ext_modules=cythonize(ext_modules, compiler_directives={"language_level": "3"}),
    zip_safe=False,
    # Add options for the build_ext command
    options={
        "build_ext": {
            "build_lib": output_dir,  # Set the custom output directory
            "force": True,  # Force recompilation of all files
        }
    },
)
