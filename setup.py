from setuptools import setup, find_packages

setup(
    name="pipemagic",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.71.0",
        "gitpython>=3.1.44",
        "python-dotenv>=1.1.0"
    ],
    author="Marlon Souza",
    author_email="your.email@example.com",
    description="An AI-powered code review tool for GitHub Actions",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/pipemagic",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)