import setuptools
import subprocess
import os

jamf_version = (
    subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
    .stdout.decode("utf-8")
    .strip()
)
#assert "." in jamf_version

assert os.path.isfile("jamf/version.py")
with open("jamf/VERSION", "w", encoding="utf-8") as fh:
    fh.write(f"{jamf_version}\n")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-jamf",
    version=jamf_version,
    author="The University of Utah",
    author_email="mlib-its-mac@lists.utah.edu",
    description="Python wrapper for Jamf Pro API",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/univ-of-utah-marriott-library-apple/python-jamf",
    packages=setuptools.find_packages(),
    package_data={'jamf': ['*.json', 'VERSION']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['conf-python-jamf=jamf.setconfig:main']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        # 4 - Beta
        # 5 - Production/Stable
        "Development Status :: 4 - Beta",
    ],
    python_requires='>=3.6',
    install_requires=['requests>=2.24.0','keyring>=23.0.0'],
)