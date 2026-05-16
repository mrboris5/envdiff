"""Sort .env file keys alphabetically or by custom order."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class SortResult:
    source: str
    original_lines: List[str]
    sorted_lines: List[str]
    moved_keys: List[str] = field(default_factory=list)

    @property
    def was_changed(self) -> bool:
        return self.original_lines != self.sorted_lines

    def to_env_string(self) -> str:
        return "\n".join(self.sorted_lines)


def _is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _key_from_line(line: str) -> Optional[str]:
    stripped = line.strip()
    if _is_comment_or_blank(stripped):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export "):].strip()
    if "=" in stripped:
        return stripped.split("=", 1)[0].strip()
    return None


def sort_env_lines(
    lines: List[str],
    source: str = "<input>",
    custom_order: Optional[List[str]] = None,
    group_comments: bool = True,
) -> SortResult:
    """
    Sort env lines alphabetically (or by custom_order if provided).
    Comments immediately preceding a key are kept attached to that key.
    """
    original = list(lines)

    # Group lines into blocks: leading comments + key line
    blocks: List[List[str]] = []
    current_comments: List[str] = []

    for line in lines:
        if _is_comment_or_blank(line.strip()) and group_comments:
            current_comments.append(line)
        else:
            blocks.append(current_comments + [line])
            current_comments = []

    # Flush trailing comments
    if current_comments:
        blocks.append(current_comments)

    def block_sort_key(block: List[str]) -> str:
        for bl in block:
            k = _key_from_line(bl)
            if k is not None:
                if custom_order and k in custom_order:
                    idx = custom_order.index(k)
                    return f"\x00{idx:06d}"
                return k.lower()
        return "\xff"  # trailing comment/blank blocks go last

    sorted_blocks = sorted(blocks, key=block_sort_key)

    sorted_lines: List[str] = []
    for block in sorted_blocks:
        sorted_lines.extend(block)

    moved: List[str] = []
    orig_keys = [_key_from_line(l) for l in original if _key_from_line(l)]
    sort_keys = [_key_from_line(l) for l in sorted_lines if _key_from_line(l)]
    for i, (o, s) in enumerate(zip(orig_keys, sort_keys)):
        if o != s:
            moved.append(s)

    return SortResult(
        source=source,
        original_lines=original,
        sorted_lines=sorted_lines,
        moved_keys=list(dict.fromkeys(moved)),
    )


def sort_env_file(path: str, **kwargs) -> SortResult:
    with open(path, "r") as fh:
        lines = fh.read().splitlines()
    return sort_env_lines(lines, source=path, **kwargs)
