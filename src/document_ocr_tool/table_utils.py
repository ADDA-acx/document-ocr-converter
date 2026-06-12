from __future__ import annotations

from statistics import median
from typing import Any

from .layout_utils import cluster_lines, line_to_text, normalize_items


def detect_simple_table(items: list[dict[str, Any]], min_score: float = 0.45) -> list[list[str]] | None:
    """启发式表格识别：只处理行列对齐明显的简单表格，复杂表格会降级为普通文本。"""
    normalized = normalize_items(items, min_score)
    lines = cluster_lines(normalized)
    candidate_lines = [line for line in lines if len(line) >= 2]
    if len(candidate_lines) < 2:
        return None

    x_positions = []
    for line in candidate_lines:
        x_positions.extend(item["x1"] for item in line)
    if len(x_positions) < 4:
        return None

    heights = [item["height"] for line in candidate_lines for item in line]
    tolerance = max(18.0, median(heights) * 1.4)
    columns: list[float] = []
    for x in sorted(x_positions):
        matched = False
        for index, col_x in enumerate(columns):
            if abs(x - col_x) <= tolerance:
                columns[index] = (col_x + x) / 2
                matched = True
                break
        if not matched:
            columns.append(x)

    if len(columns) < 2:
        return None

    aligned_rows = 0
    table: list[list[str]] = []
    for line in candidate_lines:
        row = [""] * len(columns)
        hits = 0
        for item in line:
            distances = [abs(item["x1"] - col_x) for col_x in columns]
            col_index = distances.index(min(distances))
            if distances[col_index] <= tolerance:
                row[col_index] = (row[col_index] + " " + item["text"]).strip()
                hits += 1
        if hits >= 2:
            aligned_rows += 1
            table.append(row)

    coverage = aligned_rows / max(1, len(candidate_lines))
    if aligned_rows >= 2 and coverage >= 0.65:
        return table
    return None


def fallback_text_rows(items: list[dict[str, Any]]) -> list[str]:
    return [line_to_text(line) for line in cluster_lines(normalize_items(items)) if line]
