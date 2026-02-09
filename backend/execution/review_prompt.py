"""
TrustLens AI - Review Prompt Loader
审核 Prompt 加载与规则实例化模块
"""
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ReviewContext:
    """审核上下文"""
    rule_id: str
    rule_name: str
    category: str
    rule_type: str
    risk_level: str
    intent: str
    params: Dict[str, Any]
    chunks: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category,
            "rule_type": self.rule_type,
            "risk_level": self.risk_level,
            "intent": self.intent,
            "params": self.params,
            "chunks": self.chunks,
        }


class ReviewPromptLoader:
    """审核 Prompt 加载器"""

    def __init__(self, prompt_path: str = None):
        """
        初始化 Prompt 加载器

        Args:
            prompt_path: Prompt 模板文件路径
        """
        if prompt_path is None:
            # 默认路径 - 项目根目录的 prompts 文件夹
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            prompt_path = os.path.join(
                project_root,
                "prompts",
                "review.txt"
            )

        self.prompt_path = prompt_path
        self._template = None

    def load_template(self) -> str:
        """加载 Prompt 模板"""
        if self._template is None:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                self._template = f.read()
        return self._template

    def build_prompt(
        self,
        rule: Dict[str, Any],
        chunks: List[Dict[str, Any]],
    ) -> str:
        """
        构建完整的审核 Prompt

        Args:
            rule: 规则字典
            chunks: 候选原文 chunks

        Returns:
            完整的 Prompt 文本
        """
        template = self.load_template()

        # 格式化规则参数
        params = rule.get("params", {})
        params_formatted = self._format_params(params)

        # 格式化 chunks
        chunks_formatted = self._format_chunks(chunks)

        # 替换占位符
        prompt = template.format(
            rule_id=rule.get("rule_id", ""),
            rule_name=rule.get("name", ""),
            category=rule.get("category", ""),
            rule_type=rule.get("type", ""),
            risk_level=rule.get("risk_level", ""),
            intent=rule.get("intent", ""),
            params_formatted=params_formatted,
            chunks_formatted=chunks_formatted,
        )

        return prompt

    def _format_params(self, params: Dict[str, Any]) -> str:
        """格式化规则参数"""
        if not params:
            return "  （无参数）"

        lines = []
        for key, value in params.items():
            if isinstance(value, (int, float)):
                lines.append(f"  - {key}: {value}")
            elif isinstance(value, str):
                lines.append(f"  - {key}: \"{value}\"")
            elif isinstance(value, list):
                lines.append(f"  - {key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"  - {key}: {value}")

        return "\n".join(lines)

    def _format_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """格式化候选原文"""
        if not chunks:
            return "（未提供候选原文）"

        lines = []
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id", f"chunk_{i}")
            page = chunk.get("page", "?")
            text = chunk.get("text", "")

            lines.append(f"\n--- 片段 {i+1} ---")
            lines.append(f"Chunk ID: {chunk_id}")
            lines.append(f"页码: 第 {page} 页")
            lines.append(f"原文:")
            lines.append(f"  {text}")

        return "\n".join(lines)

    def build_prompt_from_context(self, context: ReviewContext) -> str:
        """
        从审核上下文构建 Prompt

        Args:
            context: 审核上下文对象

        Returns:
            完整的 Prompt 文本
        """
        return self.build_prompt(
            rule={
                "rule_id": context.rule_id,
                "name": context.rule_name,
                "category": context.category,
                "type": context.rule_type,
                "risk_level": context.risk_level,
                "intent": context.intent,
                "params": context.params,
            },
            chunks=context.chunks,
        )


def load_review_prompt(prompt_path: str = None) -> str:
    """
    便捷函数：加载审核 Prompt 模板

    Args:
        prompt_path: Prompt 文件路径

    Returns:
        Prompt 模板内容
    """
    loader = ReviewPromptLoader(prompt_path)
    return loader.load_template()


def build_review_prompt(
    rule: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    prompt_path: str = None,
) -> str:
    """
    便捷函数：构建审核 Prompt

    Args:
        rule: 规则字典
        chunks: 候选原文 chunks
        prompt_path: Prompt 文件路径

    Returns:
        完整的 Prompt 文本
    """
    loader = ReviewPromptLoader(prompt_path)
    return loader.build_prompt(rule, chunks)


class ReviewPromptValidator:
    """审核 Prompt 验证器"""

    def validate_prompt_output(self, output: str) -> Dict[str, Any]:
        """
        验证 LLM 输出是否符合 ReviewResult Schema

        Args:
            output: LLM 输出文本

        Returns:
            验证结果和解析后的数据
        """
        result = {
            "valid": False,
            "error": None,
            "data": None,
        }

        # 尝试解析 JSON
        try:
            # 清理输出：移除可能的 markdown 代码块标记
            output = output.strip()
            if output.startswith("```json"):
                output = output[7:]
            if output.startswith("```"):
                output = output[3:]
            if output.endswith("```"):
                output = output[:-3]
            output = output.strip()

            data = json.loads(output)

            # 验证必需字段
            required_fields = ["rule_id", "status", "reason"]
            for field in required_fields:
                if field not in data:
                    result["error"] = f"Missing required field: {field}"
                    return result

            # 验证 status 值
            valid_statuses = ["PASS", "RISK", "MISSING"]
            if data["status"] not in valid_statuses:
                result["error"] = f"Invalid status: {data['status']}. Must be one of {valid_statuses}"
                return result

            # 验证 evidence
            if "evidence" in data:
                if not isinstance(data["evidence"], list):
                    result["error"] = "evidence must be an array"
                    return result

                for ev in data["evidence"]:
                    if not isinstance(ev, dict):
                        result["error"] = "Each evidence item must be an object"
                        return result

                    ev_required = ["chunk_id", "page", "text"]
                    for field in ev_required:
                        if field not in ev:
                            result["error"] = f"Missing evidence field: {field}"
                            return result

            # 验证 confidence
            if "confidence" in data:
                conf = data["confidence"]
                if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
                    result["error"] = "confidence must be a number between 0 and 1"
                    return result

            result["valid"] = True
            result["data"] = data

        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON: {str(e)}"
        except Exception as e:
            result["error"] = f"Validation error: {str(e)}"

        return result


# 预定义的 Prompt 版本信息
PROMPT_VERSION = "v1.0"
PROMPT_DATE = "2026-02-09"
