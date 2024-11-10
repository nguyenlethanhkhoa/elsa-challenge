from setuptools import setup, find_packages


def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line and not line.startswith("#")]


setup(
    name='shared_package',
    version='0.1.0',
    packages=find_packages(include=['shared', 'shared.*']),
    install_requires=parse_requirements('requirements.txt'),
    author='Your Name',
    author_email='your.email@example.com',
    description='A description of your model package',
    url='https://github.com/yourusername/model_package',  # Update this URL if hosting on GitHub
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
