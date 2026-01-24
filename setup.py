"""
Setup Configuration for Pre-Visit Voice Agent
==============================================

Installation:
    pip install -e .

This installs the package in editable mode for development.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="pre-visit-voice-agent",
    version="1.0.0",
    author="EnsanAI",
    description="Real-time voice agent for pre-visit patient interviews in Egyptian Arabic",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ensanai/pre-visit-voice-agent",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9,<3.12",
    install_requires=[
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "numpy>=1.22.0,<1.27.0",
        "sounddevice>=0.4.6",
        "openai-whisper>=20231117",
        "TTS>=0.22.0",
        "scipy>=1.11.0",
        "librosa>=0.10.0",
        "numba>=0.58.0",
        "openai>=1.12.0",
        "anthropic>=0.18.0",
        "tiktoken>=0.6.0",
        "pydantic>=2.6.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pre-visit-agent=pre_visit_agent.main:main",
        ],
    },
    include_package_data=True,
)
