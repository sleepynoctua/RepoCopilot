import os
from typing import List, Generator
from pathlib import Path


class RepositoryCrawler:
    def __init__(
        self,
        root_dir: str,
        extensions: List[str] = [
            ".py",
            ".c",
            ".cpp",
            ".cc",
            ".cxx",
            ".h",
            ".hpp",
            ".hxx",
            ".hh",
            ".cs",
            ".rs",
            ".go",
            ".ts",
            ".js",
            ".java",
            ".lua",
            # Front-end & Configs
            ".html",
            ".css",
            ".scss",
            ".less",
            ".json",
            ".yaml",
            ".yml",
            ".md",
            ".xml",
            ".toml",
            ".ini",
            ".conf",
            ".gitignore",
            ".dockerfile",
            "Dockerfile",
        ],
        ignore_dirs: List[str] = None,
    ):
        self.root_dir = Path(root_dir)
        self.extensions = set(extensions)
        self.ignore_dirs = set(
            ignore_dirs
            or [
                ".git",
                "__pycache__",
                ".venv",
                "env",
                "venv",
                "node_modules",
                "runs",
                "weights",
            ]
        )

    def scan(self) -> Generator[Path, None, None]:
        """
        Yields paths to valid source files in the repository.
        """
        for root, dirs, files in os.walk(self.root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [
                d for d in dirs if d not in self.ignore_dirs and not d.startswith(".")
            ]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.extensions:
                    yield file_path


if __name__ == "__main__":
    # Test crawler
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    crawler = RepositoryCrawler(root)
    print(f"Scanning {root}...")
    for f in crawler.scan():
        print(f)
