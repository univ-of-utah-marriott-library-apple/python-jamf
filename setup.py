import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-jamf", # Replace with your own username
    version="0.4.1",
    author="The University of Utah",
    author_email="mlib-its-mac@lists.utah.edu",
    description="Maintaining & automating Jamf Pro via the API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/univ-of-utah-marriott-library-apple/jctl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)