from setuptools import setup, find_packages

setup(
    name="deepNaviSDK",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A navigation SDK for automating UI navigation and control handling on Windows.",
    long_description=open("README.md").read(),  # Optional: Add a README.md for a detailed description
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/deepNaviSDK",  # Replace with your project's URL
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "uiautomation>=1.0",   # Add your dependencies here
        "comtypes>=1.1.10",
    ],
    entry_points={
        "console_scripts": [
            "deepnavi=deepNaviSDK.cli:main",  # Optional: Add a CLI entry point if needed
        ],
    },
)
