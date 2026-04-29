from setuptools import setup, find_packages

setup(
    name="seek_digital_intelligence",
    version="1.0.0",
    description="Seek Digital — Market Intelligence Spider Suite",
    packages=find_packages(),
    install_requires=[
        "scrapy>=2.11",
        "scrapy-zyte-api>=0.22",
        "scrapy-poet>=0.21",
        "zyte-spider-templates>=0.12.0",
        "itemadapter>=0.8",
        "python-dotenv>=1.0",
        "w3lib>=2.1",
    ],
    entry_points={
        "scrapy": [
            "settings = seek_intelligence.settings",
        ],
    },
    python_requires=">=3.9",
)
