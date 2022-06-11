from skbuild import setup  # This line replaces 'from setuptools import setup'
# from setuptools import setup

setup(
    name='litgensample',
    version='0.1.0',
    author='Pascal Thomet',
    author_email='pthomet@gmail.com',
    description='litgensample, example library generated by litgen (a pybind11 automated generator)',
    url='https://github.com/pthom/litgen/example',

    packages=(["litgensample"]),
    package_dir={"": "bindings"},
    cmake_install_dir="bindings/litgensample",
    include_package_data=True,
    extras_require={"test": ["pytest"]},
    python_requires=">=3.6",
    package_data={"litgensample": ["*.pyi"]}
)
