from setuptools import setup, find_packages
from typing import List

def get_requirements(requirements_path: str) -> List[str]:
    '''This function will return the list of requirements'''
    requirements = []
    with open(requirements_path, 'r') as file:
        requirements = file.readlines()
        requirements = [req.replace('\n', '') for req in requirements]
        if "-e ." in requirements:
            requirements.remove("-e .")

    return requirements


setup(
    name='Valorant Analysis',
    version='0.1.0',
    packages=find_packages(),
    install_requires=get_requirements(requirements_path='requirements.txt'),
    description='A project to analyze Valorant game data using Python.',
    author='Swapnil Joijode',
    author_email='swapniljoijode22@gmail.com'
)