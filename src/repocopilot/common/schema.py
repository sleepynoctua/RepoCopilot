from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ChunkType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    BLOCK = "block"  # General code block if not function/class
    DOCSTRING = "docstring"


class CodeChunk(BaseModel):
    id: str = Field(..., description="Unique identifier (e.g., hash of content + path)")
    content: str
    file_path: str
    start_line: int
    end_line: int
    type: ChunkType

    # Metadata for retrieval boosting
    name: Optional[str] = None  # Function or Class name
    parent_name: Optional[str] = None  # Class name if it's a method

    # Optional: AST-derived context (e.g., imports used, function calls)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True  # Make instances immutable


class SearchResult(BaseModel):
    chunk: CodeChunk
    score: float
    source: str = "vector"  # 'vector', 'bm25', or 'hybrid'
