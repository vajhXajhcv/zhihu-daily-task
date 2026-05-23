"""
内容质量审查模块（六维检查）。

维度：
  1. 字数检查    - 确保篇幅在合理区间
  2. 关键词检查  - 拦截 AI 套话、营销用语、禁用词
  3. 格式检查    - 确保无 Markdown、无序号、无模板化过渡词
  4. 重复检查    - 检测段落/句子重复、内容冗余
  5. 可读性检查  - 句长分布、标点使用、信息密度
  6. 语气检查    - 拦截说教口吻、营销语气、空洞升华

使用：
    from reviewer import ContentReviewer
    reviewer = ContentReviewer()
    result = reviewer.review(content, topic)
    if not result["passed"]:
        print(result["report"])
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


# ---------- 审查规则配置 ----------

# AI 套话与模板化过渡词（prompt 里已禁止，这里做二次拦截）
AI_CLICHES = [
    "首先", "其次", "再次", "最后",
    "然而", "因此", "综上所述", "总而言之", "总的来说",
    "值得注意的是", "不可否认的是", "不可否认的是",
    "让我们来看", "不难发现", "显而易见",
    "随着.*?的发展", "在当今社会", "在数字化时代",
    "一方面.*?另一方面",
]

# 营销用语
MARKETING_WORDS = [
    "快来", "千万不要错过", "限时", "免费领取",
    "爆款", "神器", "绝绝子", "YYDS", "宝藏",
    "赶紧", "立即行动", "错过再等一年",
]

# 说教口吻
PREACHY_PATTERNS = [
    "你应当", "你必须", "你应该", "你不能",
    "我们要", "大家必须", "每个人都应该",
]

# 空洞升华
EMPTY_ELEVATION = [
    "人生的意义", "时代的浪潮", "历史的洪流",
    "照亮前行的路", "永垂不朽", "万古流芳",
    "不禁让人深思", "引人深思",
]

# 格式违规：Markdown 标记
MARKDOWN_PATTERNS = [
    (r"^#{1,6}\s+", "Markdown 标题标记"),
    (r"\*\*.*?\*\*", "Markdown 加粗"),
    (r"`{3}.*?\n", "Markdown 代码块"),
    (r"`[^`]+`", "Markdown 行内代码"),
    (r"^\s*[-*+]\s+", "Markdown 列表项"),
    (r"^\s*\d+\.\s+", "数字序号"),
]

# 格式违规：模板化过渡词（已在 AI_CLICHES 中，但这里单独检查序号词）
SEQUENCE_WORDS = ["第一", "第二", "第三", "第四", "第五"]


@dataclass
class DimensionResult:
    name: str
    score: float          # 0-100
    passed: bool
    issues: list[str] = field(default_factory=list)


class ContentReviewer:
    """内容质量审查器。"""

    def __init__(
        self,
        min_words: int = 800,
        max_words: int = 4000,
        min_score: float = 75.0,
        forbidden_words: list[str] | None = None,
    ):
        self.min_words = min_words
        self.max_words = max_words
        self.min_score = min_score
        self.forbidden_words = forbidden_words or []

    # ---------- 六维检查方法 ----------

    def _check_word_count(self, text: str) -> DimensionResult:
        """字数检查。中文按字计，英文按词计（简单估算）。"""
        # 中文字符数
        cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # 英文单词数（简单估算）
        en_words = len(re.findall(r"[a-zA-Z]+", text))
        total = cn_chars + en_words

        issues = []
        if total < self.min_words:
            issues.append(f"字数不足：{total}（要求至少 {self.min_words}）")
        if total > self.max_words:
            issues.append(f"字数过多：{total}（要求不超过 {self.max_words}）")

        # 计分：在区间中间得 100，偏离线性下降
        if self.min_words <= total <= self.max_words:
            score = 100.0
        elif total < self.min_words:
            score = max(0, 100 * total / self.min_words)
        else:
            score = max(0, 100 * self.max_words / total)

        return DimensionResult(
            name="字数检查",
            score=round(score, 1),
            passed=len(issues) == 0,
            issues=issues,
        )

    def _check_keywords(self, text: str) -> DimensionResult:
        """关键词检查：拦截 AI 套话、营销用语、用户自定义禁用词。"""
        issues = []
        found_cliches = set()
        found_marketing = set()
        found_custom = set()

        for pattern in AI_CLICHES:
            for match in re.finditer(pattern, text):
                found_cliches.add(match.group(0)[:20])

        for word in MARKETING_WORDS:
            if word in text:
                found_marketing.add(word)

        for word in self.forbidden_words:
            if word in text:
                found_custom.add(word)

        if found_cliches:
            issues.append(f"AI 套话/模板词：{', '.join(sorted(found_cliches))}")
        if found_marketing:
            issues.append(f"营销用语：{', '.join(sorted(found_marketing))}")
        if found_custom:
            issues.append(f"自定义禁用词：{', '.join(sorted(found_custom))}")

        # 每出现一个违规词扣 10 分，最多扣完
        penalty = (len(found_cliches) + len(found_marketing) + len(found_custom)) * 10
        score = max(0, 100 - penalty)

        return DimensionResult(
            name="关键词检查",
            score=round(score, 1),
            passed=score >= 60,
            issues=issues,
        )

    def _check_format(self, text: str) -> DimensionResult:
        """格式检查：Markdown 标记、序号、模板化过渡词。"""
        issues = []

        for pattern, desc in MARKDOWN_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                issues.append(f"{desc}：发现 {len(matches)} 处")

        found_seq = [w for w in SEQUENCE_WORDS if w in text]
        if found_seq:
            issues.append(f"序号词：{', '.join(found_seq)}")

        # 检查空行是否足够（段落分隔）
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) < 3:
            issues.append(f"段落过少：仅 {len(paragraphs)} 段，建议至少 3 段")

        penalty = min(len(issues) * 15, 100)
        score = 100 - penalty

        return DimensionResult(
            name="格式检查",
            score=round(score, 1),
            passed=len(issues) == 0,
            issues=issues,
        )

    def _check_repetition(self, text: str) -> DimensionResult:
        """重复检查：检测相邻段落相似度、重复句子。"""
        issues = []
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 10]

        # 1. 相邻段落相似度（简单：共同子串比例）
        repeat_pairs = 0
        for i in range(len(paragraphs) - 1):
            a, b = paragraphs[i], paragraphs[i + 1]
            sim = self._simple_similarity(a, b)
            if sim > 0.6:
                repeat_pairs += 1
                preview = a[:30] + "..."
                issues.append(f"相邻段落重复度 {sim:.0%}：{preview}")

        # 2. 完全重复的句子
        sentences = re.split(r"[。！？\n]", text)
        seen = set()
        dup_sentences = 0
        for s in sentences:
            s_clean = re.sub(r"\s+", "", s.strip())
            if len(s_clean) > 10:
                if s_clean in seen:
                    dup_sentences += 1
                seen.add(s_clean)

        if dup_sentences:
            issues.append(f"完全重复句子：{dup_sentences} 句")

        penalty = repeat_pairs * 20 + dup_sentences * 15
        score = max(0, 100 - penalty)

        return DimensionResult(
            name="重复检查",
            score=round(score, 1),
            passed=score >= 70,
            issues=issues,
        )

    def _check_readability(self, text: str) -> DimensionResult:
        """可读性检查：句长分布、超长句、标点密度。"""
        issues = []
        sentences = [s.strip() for s in re.split(r"[。！？]", text) if s.strip()]

        if not sentences:
            return DimensionResult(name="可读性检查", score=0, passed=False, issues=["无有效句子"])

        lengths = [len(s) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        long_sentences = [l for l in lengths if l > 80]

        if avg_len > 50:
            issues.append(f"平均句长过长：{avg_len:.0f} 字（建议 < 40）")
        if long_sentences:
            issues.append(f"超长句（>80字）：{len(long_sentences)} 句")
        if len(sentences) < 10:
            issues.append(f"句子数过少：{len(sentences)} 句")

        # 计分：平均句长 20-35 最佳
        if avg_len <= 35:
            score = 100 - len(long_sentences) * 5
        elif avg_len <= 50:
            score = 80 - len(long_sentences) * 5
        else:
            score = 60 - len(long_sentences) * 5
        score = max(0, score)

        return DimensionResult(
            name="可读性检查",
            score=round(score, 1),
            passed=score >= 60,
            issues=issues,
        )

    def _check_tone(self, text: str) -> DimensionResult:
        """语气检查：说教口吻、营销语气、空洞升华。"""
        issues = []
        found_preachy = set()
        found_empty = set()

        for pattern in PREACHY_PATTERNS:
            for match in re.finditer(pattern, text):
                found_preachy.add(match.group(0))

        for phrase in EMPTY_ELEVATION:
            if phrase in text:
                found_empty.add(phrase)

        if found_preachy:
            issues.append(f"说教口吻：{', '.join(sorted(found_preachy))}")
        if found_empty:
            issues.append(f"空洞升华：{', '.join(sorted(found_empty))}")

        # 检查感叹号密度（营销常见）
        exclaim_count = text.count("！")
        if exclaim_count > 5:
            issues.append(f"感叹号过多：{exclaim_count} 个（易显营销感）")

        penalty = len(found_preachy) * 15 + len(found_empty) * 10 + (exclaim_count > 5) * 10
        score = max(0, 100 - penalty)

        return DimensionResult(
            name="语气检查",
            score=round(score, 1),
            passed=score >= 70,
            issues=issues,
        )

    # ---------- 工具方法 ----------

    def _simple_similarity(self, a: str, b: str) -> float:
        """简单相似度：基于字符集合的 Jaccard 近似。"""
        set_a = set(a)
        set_b = set(b)
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union else 0.0

    # ---------- 主入口 ----------

    def review(self, content: str, topic: str = "") -> dict:
        """
        执行六维审查。

        Returns:
            {
                "passed": bool,
                "total_score": float,
                "dimensions": [DimensionResult, ...],
                "issues": [str, ...],
                "report": str,   # 人类可读报告
            }
        """
        dimensions = [
            self._check_word_count(content),
            self._check_keywords(content),
            self._check_format(content),
            self._check_repetition(content),
            self._check_readability(content),
            self._check_tone(content),
        ]

        total_score = sum(d.score for d in dimensions) / len(dimensions)
        passed = total_score >= self.min_score and all(d.passed for d in dimensions)

        all_issues = []
        for d in dimensions:
            all_issues.extend([f"[{d.name}] {issue}" for issue in d.issues])

        report_lines = [
            f"内容审查报告（话题：{topic or '未指定'}）",
            f"总分：{total_score:.1f}/100（及格线：{self.min_score}）",
            f"结果：{'✅ 通过' if passed else '❌ 未通过'}",
            "",
            "各维度得分：",
        ]
        for d in dimensions:
            flag = "✅" if d.passed else "❌"
            report_lines.append(f"  {flag} {d.name}: {d.score}")

        if all_issues:
            report_lines.extend(["", "问题列表："])
            for issue in all_issues:
                report_lines.append(f"  - {issue}")
        else:
            report_lines.extend(["", "未发现明显问题。"])

        return {
            "passed": passed,
            "total_score": round(total_score, 1),
            "dimensions": dimensions,
            "issues": all_issues,
            "report": "\n".join(report_lines),
        }


# ---------- CLI 测试 ----------

def main():
    import sys
    import io

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    reviewer = ContentReviewer()

    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = """首先，我们来看一下这个问题。

值得注意的是，在当今社会，随着人工智能的发展，我们发现了一个不可否认的事实。

让我们来看一个例子。快来免费领取这个神器吧！你应当立即行动。

总的来说，这个问题的答案是显而易见的，不禁让人深思人生的意义。

快来免费领取这个神器吧！
"""

    result = reviewer.review(text, topic="测试话题")
    print(result["report"])
    print(f"\n最终判定：{'通过' if result['passed'] else '未通过，禁止发布'}")


if __name__ == "__main__":
    main()
