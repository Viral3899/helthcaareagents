from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="healthcare-management-system",
    version="1.0.0",
    author="Healthcare Management Team",
    author_email="team@healthcare-system.com",
    description="AI-powered healthcare management system with intelligent agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/healthcare-management-system",
        packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "docker": [
            "docker>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # To run main.py directly, ensure PYTHONPATH=src or use the console script below
            "healthcare-system=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.sql", "*.yml", "*.yaml"],
    },
    keywords="healthcare, ai, agents, langchain, medical, hospital, management",
    project_urls={
        "Bug Reports": "https://github.com/healthcare-management-system/issues",
        "Source": "https://github.com/healthcare-management-system",
        "Documentation": "https://healthcare-management-system.readthedocs.io/",
    },
)
