import json
import os
from typing import List, Literal, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

MODEL_NAME = "gpt-4o-mini"
SUMMARIZE_MAX_TOKENS = 400
SENTIMENT_MAX_TOKENS = 250

app = FastAPI(title="Week 1 Assignment API")
load_dotenv()
client = OpenAI()


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Document(BaseModel):
    id: str
    title: str
    content: str
    source: str


class Citation(BaseModel):
    id: str
    source: str


class SummarizeRequest(BaseModel):
    input_text: str
    documents: Optional[List[Document]] = None
    summary_type: Literal["bullet", "paragraph"] = "paragraph"
    max_words: int = Field(default=120, ge=20, le=500)
    include_citations: bool = True
    prompt_variant: Literal["A", "B", "C"] = "A"


class SummarizeResponse(BaseModel):
    summary: str
    citations: List[Citation]
    model: str
    usage: Usage


class AspectSentiment(BaseModel):
    aspect: str
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    confidence: float
    rationale: str


class AnalyzeSentimentRequest(BaseModel):
    input_text: str
    documents: Optional[List[Document]] = None
    granularity: Literal["overall", "aspect"] = "overall"
    aspects: Optional[List[str]] = None
    return_rationale: bool = True
    prompt_variant: Literal["A", "B", "C"] = "A"


class AnalyzeSentimentResponse(BaseModel):
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    confidence: float
    rationale: str
    aspect_sentiments: List[AspectSentiment]
    model: str
    usage: Usage


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message}}, status_code=status_code
    )


def format_documents(documents: Optional[List[Document]]) -> str:
    if not documents:
        return "No documents provided."
    rendered = []
    for doc in documents:
        rendered.append(
            f"- id: {doc.id}\n"
            f"  title: {doc.title}\n"
            f"  source: {doc.source}\n"
            f"  content: {doc.content}"
        )
    return "\n".join(rendered)


def summarize_prompt(req: SummarizeRequest) -> List[dict]:
    documents_text = format_documents(req.documents)
    if req.prompt_variant == "B":
        system = (
            "You are an expert technical writer. Produce concise, high-signal "
            "summaries that help downstream agents decide what to retrieve next."
        )
        constraints = (
            f"- Use summary_type: {req.summary_type}\n"
            "- Emphasize key decisions, outcomes, and open questions.\n"
            "- If evidence is in documents, include citations for those points.\n"
            "- Output JSON only."
        )
        example = (
            "Example:\n"
            "Input text:\n"
            "The beta rollout improved performance but raised hosting costs. "
            "Support tickets dropped after fixing login issues.\n"
            "Documents:\n"
            "- id: ex-1\n"
            "  title: Beta Report\n"
            "  source: internal\n"
            "  content: Performance improved 15%; hosting costs +10%. "
            "Login bug fix reduced tickets.\n"
            "Output JSON:\n"
            '{ "summary": "- Performance improved 15% during beta.\n'
            '- Hosting costs rose 10%.\n'
            '- Login fix reduced support tickets.", '
            '"citations": [{"id": "ex-1", "source": "internal"}] }'
        )
    elif req.prompt_variant == "C":
        system = (
            "You are a project analyst in a multi-agent RAG workflow. Summaries "
            "must be actionable and accurate."
        )
        constraints = (
            "- If summary_type is bullet, use 3–7 bullets.\n"
            "- Maintain neutral tone; do not add new information.\n"
            "- Use citations when documents are provided.\n"
            "- Think step-by-step internally, but output only the final JSON.\n"
            "- Output JSON only."
        )
        example = ""
    else:
        system = (
            "You are a precise summarizer in a multi-agent RAG system. When "
            "documents are provided, ground the summary in those documents and "
            "cite their ids."
        )
        constraints = (
            "- Use only facts present in the input and provided documents.\n"
            "- If documents exist, prefer them over the raw input for factual claims.\n"
            f"- Keep within max_words (soft limit): {req.max_words}.\n"
            "- Output JSON only."
        )
        example = ""

    user = (
        "Task: Summarize the input text into the requested format and length.\n\n"
        f"{example}\n\n"
        f"Input text:\n{req.input_text}\n\n"
        f"Documents:\n{documents_text}\n\n"
        f"summary_type: {req.summary_type}\n"
        f"max_words: {req.max_words}\n"
        f"include_citations: {req.include_citations}\n\n"
        "Output JSON format:\n"
        '{ "summary": "string", "citations": [{"id": "string", "source": "string"}] }'
        f"\n\nConstraints:\n{constraints}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def sentiment_prompt(req: AnalyzeSentimentRequest) -> List[dict]:
    documents_text = format_documents(req.documents)
    if req.prompt_variant == "B":
        system = (
            "You are an aspect-based sentiment analyzer. The caller may supply aspects."
        )
        constraints = (
            "- If granularity is aspect, use provided aspects; otherwise infer 3–5.\n"
            "- Keep rationales to one sentence each.\n"
            "- Output JSON only."
        )
        example = (
            "Example:\n"
            "Input text:\n"
            "The app is smooth, but the subscription fee is steep.\n"
            "granularity: aspect\n"
            "aspects: performance, pricing\n"
            "Output JSON:\n"
            '{ "sentiment": "mixed", "confidence": 0.8, '
            '"rationale": "Positive on performance, negative on pricing.", '
            '"aspect_sentiments": ['
            '{"aspect": "performance", "sentiment": "positive", "confidence": 0.9, '
            '"rationale": "Smooth experience."}, '
            '{"aspect": "pricing", "sentiment": "negative", "confidence": 0.8, '
            '"rationale": "Fee is steep."}]}'
        )
    elif req.prompt_variant == "C":
        system = (
            "You are a strict, evidence-grounded sentiment classifier in a RAG pipeline."
        )
        constraints = (
            "- If evidence conflicts, choose mixed and state the conflict briefly.\n"
            "- Avoid hedging language; express confidence numerically.\n"
            "- Think step-by-step internally, but output only the final JSON.\n"
            "- Output JSON only."
        )
        example = ""
    else:
        system = (
            "You are a sentiment analyst in a multi-agent RAG system. Ground sentiment "
            "in the provided text and documents."
        )
        constraints = (
            "- Use only the given text and documents.\n"
            "- If sentiment is mixed, explain briefly why.\n"
            "- Output JSON only."
        )
        example = ""

    aspects_text = ", ".join(req.aspects or [])
    user = (
        "Task: Determine sentiment and confidence for the input text.\n\n"
        f"{example}\n\n"
        f"Input text:\n{req.input_text}\n\n"
        f"Documents:\n{documents_text}\n\n"
        f"granularity: {req.granularity}\n"
        f"aspects: {aspects_text or 'None provided'}\n"
        f"return_rationale: {req.return_rationale}\n\n"
        "Output JSON format:\n"
        '{ "sentiment": "positive|neutral|negative|mixed", "confidence": 0.0, '
        '"rationale": "string", "aspect_sentiments": ['
        '{"aspect": "string", "sentiment": "positive|neutral|negative|mixed", '
        '"confidence": 0.0, "rationale": "string"}] }'
        f"\n\nConstraints:\n{constraints}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_json_response(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def usage_from_response(response) -> Usage:
    usage = getattr(response, "usage", None)
    if not usage:
        return Usage()
    return Usage(
        prompt_tokens=usage.prompt_tokens or 0,
        completion_tokens=usage.completion_tokens or 0,
        total_tokens=usage.total_tokens or 0,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    if not req.input_text.strip():
        return error_response("invalid_input", "input_text must be non-empty", 400)
    if not os.getenv("OPENAI_API_KEY"):
        return error_response("missing_api_key", "OPENAI_API_KEY is not set", 500)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=summarize_prompt(req),
            temperature=0.2,
            max_tokens=SUMMARIZE_MAX_TOKENS,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        return error_response("openai_error", str(exc), 500)

    content = response.choices[0].message.content or "{}"
    parsed = parse_json_response(content)
    citations = parsed.get("citations", []) if req.include_citations else []
    summary = parsed.get("summary", "")

    return SummarizeResponse(
        summary=summary,
        citations=[Citation(**c) for c in citations if "id" in c and "source" in c],
        model=MODEL_NAME,
        usage=usage_from_response(response),
    )


@app.post("/analyze-sentiment", response_model=AnalyzeSentimentResponse)
def analyze_sentiment(req: AnalyzeSentimentRequest):
    if not req.input_text.strip():
        return error_response("invalid_input", "input_text must be non-empty", 400)
    if not os.getenv("OPENAI_API_KEY"):
        return error_response("missing_api_key", "OPENAI_API_KEY is not set", 500)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=sentiment_prompt(req),
            temperature=0.2,
            max_tokens=SENTIMENT_MAX_TOKENS,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        return error_response("openai_error", str(exc), 500)

    content = response.choices[0].message.content or "{}"
    parsed = parse_json_response(content)

    aspect_sentiments = []
    if req.granularity == "aspect":
        for item in parsed.get("aspect_sentiments", []) or []:
            if {"aspect", "sentiment", "confidence", "rationale"}.issubset(item):
                aspect_sentiments.append(AspectSentiment(**item))

    rationale = parsed.get("rationale", "") if req.return_rationale else ""

    return AnalyzeSentimentResponse(
        sentiment=parsed.get("sentiment", "neutral"),
        confidence=float(parsed.get("confidence", 0.0)),
        rationale=rationale,
        aspect_sentiments=aspect_sentiments,
        model=MODEL_NAME,
        usage=usage_from_response(response),
    )
