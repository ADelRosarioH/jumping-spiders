from setuptools import setup, find_packages
setup(
    name='jumping-spiders',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,  
    entry_points={'scrapy':['settings=jumping_spiders.settings']},
)