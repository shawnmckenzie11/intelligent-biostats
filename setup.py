from setuptools import setup, find_packages

setup(
    name="intelligent-biostats",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'pandas',
        'numpy',
        'scipy',
        'scikit-learn',
    ],
)
