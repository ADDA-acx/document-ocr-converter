from __future__ import annotations

import re
from statistics import median
from typing import Any


def box_bounds(box: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    return min(xs), min(ys), max(xs), max(ys)


def normalize_items(items: list[dict[str, Any]], min_score: float = 0.45) -> list[dict[str, Any]]:
    normalized = []
    for item in items:
        text = str(item.get("text", "")).strip()
        score = float(item.get("score", 0.0) or 0.0)
        box = item.get("box")
        if not text or score < min_score or not box:
            continue
        x1, y1, x2, y2 = box_bounds(box)
        normalized.append(
            {
                "text": text,
                "score": score,
                "box": box,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "height": max(1.0, y2 - y1),
            }
        )
    return sorted(normalized, key=lambda item: (item["y1"], item["x1"]))


def cluster_lines(items: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    if not items:
        return []
    heights = [item["height"] for item in items]
    tolerance = max(8.0, median(heights) * 0.65)
    lines: list[list[dict[str, Any]]] = []
    for item in items:
        center_y = (item["y1"] + item["y2"]) / 2
        placed = False
        for line in lines:
            line_center = median([(i["y1"] + i["y2"]) / 2 for i in line])
            if abs(center_y - line_center) <= tolerance:
                line.append(item)
                placed = True
                break
        if not placed:
            lines.append([item])
    for line in lines:
        line.sort(key=lambda item: item["x1"])
    return sorted(lines, key=lambda line: min(item["y1"] for item in line))


def _is_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _needs_space(left: str, right: str, gap: float, avg_height: float) -> bool:
    if not left or not right:
        return False
    if _is_cjk(left[-1]) or _is_cjk(right[0]):
        return gap > avg_height * 1.4
    if re.match(r"[\s,.;:!?)]", right[0]) or left[-1] in "([/":
        return False
    return gap > avg_height * 0.18


def line_to_text(line: list[dict[str, Any]]) -> str:
    if not line:
        return ""
    avg_height = sum(item["height"] for item in line) / len(line)
    parts = [line[0]["text"]]
    previous = line[0]
    for item in line[1:]:
        gap = item["x1"] - previous["x2"]
        if _needs_space(parts[-1], item["text"], gap, avg_height):
            parts.append(" ")
        parts.append(item["text"])
        previous = item
    return "".join(parts).strip()


def _keep_line_break(text: str) -> bool:
    return bool(
        re.match(r"^(\d+[\.)、]|[一二三四五六七八九十]+[、.]|[-•·])", text)
        or re.search(r"[:：]$", text)
        or re.match(r"^\d{4}[-/年]", text)
        or len(text) <= 18
    )


def build_paragraphs(items: list[dict[str, Any]], min_score: float = 0.45) -> list[str]:
    normalized = normalize_items(items, min_score)
    lines = cluster_lines(normalized)
    if not lines:
        return []

    line_records = []
    for line in lines:
        line_records.append(
            {
                "text": line_to_text(line),
                "y1": min(item["y1"] for item in line),
                "y2": max(item["y2"] for item in line),
                "height": median([item["height"] for item in line]),
            }
        )
    gaps = [
        max(0.0, line_records[index]["y1"] - line_records[index - 1]["y2"])
        for index in range(1, len(line_records))
    ]
    typical_gap = median(gaps) if gaps else 0.0

    paragraphs: list[str] = []
    current = ""
    for index, record in enumerate(line_records):
        text = record["text"]
        if not text:
            continue
        gap = 0.0 if index == 0 else max(0.0, record["y1"] - line_records[index - 1]["y2"])
        new_para = index == 0 or gap > max(record["height"] * 0.8, typical_gap * 1.7) or _keep_line_break(text)
        if new_para:
            if current:
                paragraphs.append(current.strip())
            current = text
        else:
            if _is_cjk(current[-1:]) or _is_cjk(text[:1]):
                current += text
            else:
                current += " " + text
    if current:
        paragraphs.append(current.strip())
    return paragraphs
