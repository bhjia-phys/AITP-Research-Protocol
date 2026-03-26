from __future__ import annotations

from pathlib import Path
from setuptools import setup, find_packages


ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
REQUIREMENTS = [
    line.strip()
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
]


setup(
    name="aitp-kernel",
    version="0.4.0",
    author="Bohan Jia",
    description="AITP runtime CLI, MCP server, and agent bootstrap assets",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/bhjia-phys/AITP-Research-Protocol",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    python_requires=">=3.10",
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "aitp=knowledge_hub.aitp_cli:main",
            "aitp-mcp=knowledge_hub.aitp_mcp_server:main",
            "aitp-codex=knowledge_hub.aitp_codex:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
