from distutils.core import setup

setup(
    # Application name:
    name="SEOSuite",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Say Media",

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="http://pypi.python.org/pypi/MyApplication_v010/",

    #
    license="LICENSE-MIT",
    description="A suite of SEO tools.",

    long_description=open("README.md").read(),

    # Dependent packages (distributions)
    install_requires=[
        'MySQL-python>=1.2.5',
        'PyYAML>=3.10',
        'requests',
        'beautifulsoup4',
        'lxml',
    ],
)