import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from typing import List, Any, Optional
import hashlib
from ..common.schema import CodeChunk, ChunkType


class CodeParser:
    def __init__(self):
        self.py_language = Language(tspython.language())
        self.parser = Parser(self.py_language)

    def parse_code(self, code: str) -> Any:
        return self.parser.parse(bytes(code, "utf8"))

    def extract_structures(self, code: str, file_path: str) -> List[CodeChunk]:
        """
        Extracts functions and classes from the code and returns CodeChunk objects.
        """
        tree = self.parse_code(code)
        root_node = tree.root_node

        chunks = []
        self._recursive_extract(root_node, code, file_path, chunks)
        return chunks

    def _recursive_extract(
        self,
        node,
        code: str,
        file_path: str,
        chunks: List[CodeChunk],
        parent_name: Optional[str] = None,
    ):
        node_type = node.type

        if node_type in ["function_definition", "class_definition"]:
            name = self._get_name(node, code)
            full_name = f"{parent_name}.{name}" if parent_name else name

            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            content = code[node.start_byte : node.end_byte]

            chunk_type = (
                ChunkType.FUNCTION
                if node_type == "function_definition"
                else ChunkType.CLASS
            )

            chunk = CodeChunk(
                id=self._generate_id(file_path, start_line),
                content=content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                type=chunk_type,
                name=name,
                parent_name=parent_name,
            )
            chunks.append(chunk)

            # Continue recursion for nested structures
            for child in node.children:
                self._recursive_extract(child, code, file_path, chunks, full_name)
        else:
            for child in node.children:
                self._recursive_extract(child, code, file_path, chunks, parent_name)

    def _get_name(self, node, code: str) -> str:
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte : child.end_byte]
        return "anonymous"

    def _generate_id(self, file_path: str, start_line: int) -> str:
        unique_str = f"{file_path}:{start_line}"
        return hashlib.md5(unique_str.encode()).hexdigest()


if __name__ == "__main__":
    # Quick test
    test_code = """
class MyClass:
    def method1(self):
        pass

def top_level_func():
    print("hello")
"""
    parser = CodeParser()
    chunks = parser.extract_structures(test_code, "test_file.py")
    for chunk in chunks:
        print(
            f"ID: {chunk.id[:8]} | Type: {chunk.type.value} | Name: {chunk.name} | Parent: {chunk.parent_name}"
        )
