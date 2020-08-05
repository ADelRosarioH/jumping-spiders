from setuptools import setup, find_packages
setup(
    name='jumping-spiders',
    version='1.0',
    packages=find_packages(),
    data_files=[('', ['user-agents.txt'])],
    entry_points={'scrapy':['settings=jumping_spiders.settings']},
)