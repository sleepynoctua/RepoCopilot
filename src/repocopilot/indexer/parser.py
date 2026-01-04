import os
from typing import List, Any
from tree_sitter import Language, Parser
from ..common.schema import CodeChunk, ChunkType

# Import languages
import tree_sitter_python as tspython
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_c_sharp as tscsharp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts
import tree_sitter_rust as tsrust
import tree_sitter_lua as tslua


class CodeParser:
    def __init__(self):
        # Map extensions to their tree-sitter language objects
        self.lang_map = {
            ".py": Language(tspython.language()),
            ".c": Language(tsc.language()),
            ".h": Language(tsc.language()),
            ".hh": Language(tscpp.language()),
            ".cpp": Language(tscpp.language()),
            ".cc": Language(tscpp.language()),
            ".cxx": Language(tscpp.language()),
            ".hpp": Language(tscpp.language()),
            ".hxx": Language(tscpp.language()),
            ".cs": Language(tscsharp.language()),
            ".go": Language(tsgo.language()),
            ".java": Language(tsjava.language()),
            ".js": Language(tsjs.language()),
            ".ts": Language(tsts.language_typescript()),
            ".tsx": Language(tsts.language_tsx()),
            ".rs": Language(tsrust.language()),
            ".lua": Language(tslua.language()),
        }
        self.parser = Parser()

        # Define node types that represent "Functions" or "Classes" for each language
        # This is a simplified mapping
        self.structure_types = {
            "function": [
                "function_definition",
                "method_definition",
                "method_declaration",
                "function_declaration",
                "function_item",
                "method_declaration_item",
            ],
            "class": [
                "class_definition",
                "class_declaration",
                "struct_specifier",
                "enum_specifier",
                "interface_declaration",
                "struct_item",
                "enum_item",
            ],
        }

    def get_language_for_file(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        return self.lang_map.get(ext)

    def extract_structures(self, code: str, file_path: str) -> List[CodeChunk]:
        lang = self.get_language_for_file(file_path)
        if not lang:
            # Fallback: if language not supported, treat as one big block
            return [
                CodeChunk(
                    id=f"{file_path}_raw",
                    content=code,
                    file_path=file_path,
                    start_line=1,
                    end_line=len(code.splitlines()),
                    type=ChunkType.BLOCK,
                )
            ]

        # New API: Instantiate parser with language
        parser = Parser(lang)
        tree = parser.parse(bytes(code, "utf8"))

        chunks = []
        self._recursive_extract(tree.root_node, code, file_path, chunks)

        # If no structures found, return the whole file
        if not chunks:
            chunks.append(
                CodeChunk(
                    id=f"{file_path}_full",
                    content=code,
                    file_path=file_path,
                    start_line=1,
                    end_line=len(code.splitlines()),
                    type=ChunkType.BLOCK,
                )
            )

        return chunks

    def _recursive_extract(
        self, node: Any, code: str, file_path: str, chunks: List[CodeChunk]
    ):
        node_type = node.type

        chunk_type = None
        if node_type in self.structure_types["function"]:
            chunk_type = ChunkType.FUNCTION
        elif node_type in self.structure_types["class"]:
            chunk_type = ChunkType.CLASS

        if chunk_type:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            content = code.splitlines()[node.start_point[0] : node.end_point[0] + 1]

            # Try to find a name for the structure
            name = None
            for child in node.children:
                if child.type == "identifier":
                    name = code[
                        child.start_byte : child.end_point[1]
                    ]  # Simplified name extraction
                    break

            chunks.append(
                CodeChunk(
                    id=f"{file_path}_{start_line}_{end_line}",
                    content="\n".join(content),
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    type=chunk_type,
                    name=name,
                )
            )
            # Usually we don't want to dive deeper once a function is found
            # to avoid duplicate nested chunks, but for classes we might want methods.
            if chunk_type == ChunkType.CLASS:
                for child in node.children:
                    self._recursive_extract(child, code, file_path, chunks)
        else:
            for child in node.children:
                self._recursive_extract(child, code, file_path, chunks)
