import json
import logging
from typing import Any
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GeneratedQuestion(BaseModel):
    question: str = Field(min_length=20)
    topic: str
    difficulty: str
    question_type: str


class EvaluatedAnswer(BaseModel):
    score: float = Field(ge=0, le=10)
    feedback: str = Field(min_length=1)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


def _client() -> OpenAI | None:
    key = get_settings().openai_api_key.strip()
    return OpenAI(api_key=key) if key else None


def _complete(system: str, user: str) -> dict[str, Any] | None:
    client = _client()
    if not client:
        return None
    response = client.chat.completions.create(
        model=get_settings().llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def generate_question_with_llm(role: str, resume_info: dict, context: dict, retrieved: list[dict]) -> GeneratedQuestion | None:
    excerpts = "\n\n".join(f"[{item['chunk_id']}] {item['text']}" for item in retrieved)
    prompt = f"""Role: {role}
Candidate resume facts (use only these): {json.dumps(resume_info)}
Interview topic: {context['topic']}
Retrieved knowledge-base excerpts (cite concepts from these, do not invent sources):
{excerpts}

Create one technically deep, personalized interview question. It must test applied or conceptual understanding, be answerable by an intern, and be grounded in the excerpts. Return JSON with exactly: question, topic, difficulty (easy|medium|hard), question_type (conceptual|applied)."""
    try:
        raw = _complete("You generate grounded technical interview questions. Return valid JSON only.", prompt)
        return GeneratedQuestion.model_validate(raw) if raw else None
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.warning("Structured question generation failed: %s", exc)
        return None
    except Exception:
        logger.exception("LLM question generation failed")
        return None


def evaluate_answer_with_llm(role: str, question: dict, answer: str, retrieved: list[dict]) -> EvaluatedAnswer | None:
    excerpts = "\n\n".join(item["text"] for item in retrieved)
    prompt = f"""Role: {role}
Question: {question['question']}
Candidate answer: {answer}
Relevant knowledge context:
{excerpts}

Evaluate only what the answer demonstrates. Do not infer experience not stated. Return JSON with exactly: score (0-10), feedback, strengths (array), improvements (array)."""
    try:
        raw = _complete("You evaluate technical interview answers fairly and concretely. Return valid JSON only.", prompt)
        return EvaluatedAnswer.model_validate(raw) if raw else None
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.warning("Structured answer evaluation failed: %s", exc)
        return None
    except Exception:
        logger.exception("LLM answer evaluation failed")
        return None
