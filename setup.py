from setuptools import setup, find_packages

setup(
    name="bible_reading_plan",
    version="0.1",
    packages=find_packages(),
    install_requires=["todoist-api-python>=2.0,<3.0"],
    author="Alex Watt",
    author_email="alex@alexcwatt.com",
    description="Push the Five Day Bible Reading Plan to Todoist",
    url="https://github.com/alexcwatt/bible-reading-plan",
    entry_points={
        "console_scripts": [
            "todoist-bible-plan = bible_reading_plan.importer:main",
        ],
    },
)
