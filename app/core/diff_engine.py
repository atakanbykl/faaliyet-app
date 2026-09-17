"""
FieldOps Assistant - Konfigürasyon Kıyaslama ve Birleştirme Motoru (Diff Engine)
Sahadan çekilen konfigürasyon ile ofis referans konfigürasyonunu kıyaslar,
görsel fark raporu üretir ve merge işlemlerini yürütür.
"""

from __future__ import annotations
import difflib
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class DiffLine:
    """Tek bir satırın kıyaslama durumu."""
    line_num_left: Optional[int]
    line_num_right: Optional[int]
    left_content: str
    right_content: str
    change_type: str  # "equal", "replace", "delete", "insert"


class ConfigDiffEngine:
    """İki konfigürasyon metnini kıyaslar ve farkları analiz eder."""

    @staticmethod
    def format_json_if_possible(text: str) -> str:
        """JSON ise okunaklı (pretty) formata getirir, değilse olduğu gibi bırakır."""
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            return text

    @classmethod
    def compare_configs(cls, baseline_text: str, field_text: str) -> Tuple[List[DiffLine], bool]:
        """
        İki konfigürasyon metnini satır satır karşılaştırır.
        (diff_lines, has_differences) ikilisi döner.
        """
        baseline_formatted = cls.format_json_if_possible(baseline_text).splitlines()
        field_formatted = cls.format_json_if_possible(field_text).splitlines()

        matcher = difflib.SequenceMatcher(None, baseline_formatted, field_formatted)
        diff_lines: List[DiffLine] = []
        has_differences = False

        left_idx = 1
        right_idx = 1

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for b_line, f_line in zip(baseline_formatted[i1:i2], field_formatted[j1:j2]):
                    diff_lines.append(DiffLine(
                        line_num_left=left_idx,
                        line_num_right=right_idx,
                        left_content=b_line,
                        right_content=f_line,
                        change_type="equal"
                    ))
                    left_idx += 1
                    right_idx += 1
            elif tag == "replace":
                has_differences = True
                # Değişen bloklar
                max_len = max(i2 - i1, j2 - j1)
                b_chunk = baseline_formatted[i1:i2]
                f_chunk = field_formatted[j1:j2]
                for k in range(max_len):
                    has_left = k < len(b_chunk)
                    has_right = k < len(f_chunk)
                    b_val = b_chunk[k] if has_left else ""
                    f_val = f_chunk[k] if has_right else ""

                    if has_left and has_right:
                        ctype = "replace"
                    elif has_right:
                        ctype = "insert"
                    else:
                        ctype = "delete"

                    diff_lines.append(DiffLine(
                        line_num_left=left_idx if has_left else None,
                        line_num_right=right_idx if has_right else None,
                        left_content=b_val,
                        right_content=f_val,
                        change_type=ctype
                    ))
                    if has_left:
                        left_idx += 1
                    if has_right:
                        right_idx += 1
            elif tag == "delete":
                has_differences = True
                for b_line in baseline_formatted[i1:i2]:
                    diff_lines.append(DiffLine(
                        line_num_left=left_idx,
                        line_num_right=None,
                        left_content=b_line,
                        right_content="",
                        change_type="delete"
                    ))
                    left_idx += 1
            elif tag == "insert":
                has_differences = True
                for f_line in field_formatted[j1:j2]:
                    diff_lines.append(DiffLine(
                        line_num_left=None,
                        line_num_right=right_idx,
                        left_content="",
                        right_content=f_line,
                        change_type="insert"
                    ))
                    right_idx += 1

        return diff_lines, has_differences

    @classmethod
    def generate_unified_patch(cls, baseline_text: str, field_text: str, filename: str = "config.json") -> str:
        """Standart git/diff formatında metinsel yama (patch) üretir."""
        b_lines = cls.format_json_if_possible(baseline_text).splitlines(keepends=True)
        f_lines = cls.format_json_if_possible(field_text).splitlines(keepends=True)
        patch = difflib.unified_diff(
            b_lines,
            f_lines,
            fromfile=f"a/{filename} (Ofis Referansı)",
            tofile=f"b/{filename} (Sahadan Çekilen)",
            lineterm=""
        )
        return "\n".join(patch)
