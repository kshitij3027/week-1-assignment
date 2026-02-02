# Part 3 — Deployment & Documentation

## Deployment
- GitHub repo: https://github.com/kshitij3027/week-1-assignment
- Render URL: https://week-1-assignment-k4yl.onrender.com

## Prompt Variants and Techniques

### /summarize — Variant A (Grounded Extractive)
Technique: Zero-shot prompting; Retrieval Augmented Generation (when documents provided).

Prompt:
```
Role/Context
You are a precise summarizer in a multi-agent RAG system. When documents are
provided, ground the summary in those documents and cite their ids.

Task
Summarize the input text into the requested format and length.

Constraints
- Use only facts present in the input and provided documents.
- If documents exist, prefer them over the raw input for factual claims.
- Keep within max_words (soft limit).
- Output JSON only.

Output Format (JSON)
{
  "summary": "string",
  "citations": [{"id": "string", "source": "string"}]
}
```

### /summarize — Variant B (Few-shot, High Signal)
Technique: Few-shot prompting; Retrieval Augmented Generation (when documents provided).

Prompt:
```
Role/Context
You are an expert technical writer. Produce concise, high-signal summaries that
help downstream agents decide what to retrieve next.

Task
Create a summary based on the input and optional documents.

Constraints
- Use summary_type to choose bullets or paragraph.
- Emphasize key decisions, outcomes, and open questions.
- If evidence is in documents, include citations for those points.
- Output JSON only.

Example:
Input text:
The beta rollout improved performance but raised hosting costs. Support tickets
dropped after fixing login issues.
Documents:
- id: ex-1
  title: Beta Report
  source: internal
  content: Performance improved 15%; hosting costs +10%. Login bug fix reduced tickets.
Output JSON:
{ "summary": "- Performance improved 15% during beta.
- Hosting costs rose 10%.
- Login fix reduced support tickets.", "citations": [{"id": "ex-1", "source": "internal"}] }

Output Format (JSON)
{
  "summary": "string",
  "citations": [{"id": "string", "source": "string"}]
}
```

### /summarize — Variant C (Chain-of-Thought, Actionable Brief)
Technique: Chain-of-thought prompting (internal reasoning only); Retrieval Augmented Generation (when documents provided).

Prompt:
```
Role/Context
You are a project analyst in a multi-agent RAG workflow. Summaries must be
actionable and accurate.

Task
Summarize the input, focusing on facts, assumptions, and next steps.

Constraints
- If summary_type is bullet, use 3–7 bullets.
- Maintain neutral tone; do not add new information.
- Use citations when documents are provided.
- Think step-by-step internally, but output only the final JSON.
- Output JSON only.

Output Format (JSON)
{
  "summary": "string",
  "citations": [{"id": "string", "source": "string"}]
}
```

### /analyze-sentiment — Variant A (Overall Sentiment)
Technique: Zero-shot prompting.

Prompt:
```
Role/Context
You are a sentiment analyst in a multi-agent RAG system. Ground sentiment in
the provided text and documents.

Task
Determine sentiment and confidence for the input text.

Constraints
- Use only the given text and documents.
- If sentiment is mixed, explain briefly why.
- Output JSON only.

Output Format (JSON)
{
  "sentiment": "positive|neutral|negative|mixed",
  "confidence": 0.0,
  "rationale": "string"
}
```

### /analyze-sentiment — Variant B (Few-shot, Aspect Focused)
Technique: Few-shot prompting.

Prompt:
```
Role/Context
You are an aspect-based sentiment analyzer. The caller may supply aspects.

Task
Return overall sentiment and aspect-level sentiment when requested.

Constraints
- If granularity is aspect, use provided aspects; otherwise infer 3–5.
- Keep rationales to one sentence each.
- Output JSON only.

Example:
Input text:
The app is smooth, but the subscription fee is steep.
granularity: aspect
aspects: performance, pricing
Output JSON:
{ "sentiment": "mixed", "confidence": 0.8, "rationale": "Positive on performance, negative on pricing.",
  "aspect_sentiments": [{"aspect": "performance", "sentiment": "positive", "confidence": 0.9, "rationale": "Smooth experience."},
  {"aspect": "pricing", "sentiment": "negative", "confidence": 0.8, "rationale": "Fee is steep."}] }

Output Format (JSON)
{
  "sentiment": "positive|neutral|negative|mixed",
  "confidence": 0.0,
  "rationale": "string",
  "aspect_sentiments": [
    {
      "aspect": "string",
      "sentiment": "positive|neutral|negative|mixed",
      "confidence": 0.0,
      "rationale": "string"
    }
  ]
}
```

### /analyze-sentiment — Variant C (Chain-of-Thought, RAG-Grounded)
Technique: Chain-of-thought prompting (internal reasoning only); Retrieval Augmented Generation (when documents provided).

Prompt:
```
Role/Context
You are a strict, evidence-grounded sentiment classifier in a RAG pipeline.

Task
Classify sentiment using the most reliable evidence from documents when
available, otherwise from the input.

Constraints
- If evidence conflicts, choose mixed and state the conflict briefly.
- Avoid hedging language; express confidence numerically.
- Think step-by-step internally, but output only the final JSON.
- Output JSON only.

Output Format (JSON)
{
  "sentiment": "positive|neutral|negative|mixed",
  "confidence": 0.0,
  "rationale": "string"
}
```

## Prompt-Variant Tests (Local)

### Input used for /summarize
```
Our onboarding redesign launched in January. The new flow reduced drop-off at step two from 28% to 14%, but churn still spikes at the pricing screen. Support reports 30% fewer activation tickets, yet enterprise customers request clearer setup guidance. Product wants to test a guided setup for enterprise trials and improve in-app education for self-serve users. The March milestone targets activation analytics, time-to-first-value tracking, and an A/B test on pricing copy.
```

### /summarize — Variant A
Response:
```
{"summary":"The onboarding redesign launched in January reduced drop-off at step two from 28% to 14%. However, churn at the pricing screen remains high. Support has seen a 30% decrease in activation tickets, but enterprise customers are requesting clearer setup guidance. Product plans to test a guided setup for enterprise trials and enhance in-app education for self-serve users. The March milestone will focus on activation analytics, time-to-first-value tracking, and an A/B test on pricing copy.","citations":[{"id":"doc-1","source":"internal-report"}],"model":"gpt-4o-mini","usage":{"prompt_tokens":330,"completion_tokens":132,"total_tokens":462}}
```

### /summarize — Variant B
Response:
```
{"summary":"- Onboarding redesign launched in January, reducing drop-off at step two from 28% to 14%.\n- Churn remains high at the pricing screen.\n- Support tickets for activation decreased by 30%.\n- Enterprise customers request clearer setup guidance; product team plans to test guided setup for trials.\n- March milestone includes activation analytics, time-to-first-value tracking, and A/B test on pricing copy.","citations":[{"id":"doc-1","source":"internal-report"}],"model":"gpt-4o-mini","usage":{"prompt_tokens":430,"completion_tokens":122,"total_tokens":552}}
```

### /summarize — Variant C
Response:
```
{"summary":"- Onboarding redesign launched in January, reducing drop-off at step two from 28% to 14%.\n- Churn still high at the pricing screen, identified as the top funnel leak.\n- Support reports a 30% decrease in activation tickets.\n- Enterprise customers request clearer setup guidance.\n- Product plans to test guided setup for enterprise trials and enhance in-app education for self-serve users.\n- March milestone includes activation analytics, time-to-first-value tracking, and A/B test on pricing copy.","citations":[{"id":"doc-1","source":"internal-report"}],"model":"gpt-4o-mini","usage":{"prompt_tokens":329,"completion_tokens":132,"total_tokens":461}}
```

### Input used for /analyze-sentiment
```
The product is fast and reliable, but the subscription price is high and customer support is slow to respond on weekends.
```

### /analyze-sentiment — Variant A
Response:
```
{"sentiment":"mixed","confidence":0.85,"rationale":"The text expresses positive sentiments about the product's speed and reliability, but also highlights negative aspects regarding the high subscription price and slow customer support on weekends. This combination of positive and negative sentiments indicates a mixed overall sentiment.","aspect_sentiments":[],"model":"gpt-4o-mini","usage":{"prompt_tokens":193,"completion_tokens":235,"total_tokens":428}}
```

### /analyze-sentiment — Variant B
Response:
```
{"sentiment":"mixed","confidence":0.85,"rationale":"Positive on performance, negative on pricing and support.","aspect_sentiments":[{"aspect":"performance","sentiment":"positive","confidence":0.9,"rationale":"Fast and reliable product."},{"aspect":"pricing","sentiment":"negative","confidence":0.8,"rationale":"Subscription price is high."},{"aspect":"support","sentiment":"negative","confidence":0.75,"rationale":"Customer support is slow to respond on weekends."}],"model":"gpt-4o-mini","usage":{"prompt_tokens":324,"completion_tokens":165,"total_tokens":489}}
```

### /analyze-sentiment — Variant C
Response:
```
{"sentiment":"mixed","confidence":0.85,"rationale":"The text contains both positive and negative sentiments. The product is described as 'fast and reliable', indicating a positive sentiment. However, the mention of 'high subscription price' and 'slow customer support on weekends' introduces negative sentiments. The overall sentiment is mixed due to these conflicting aspects.","aspect_sentiments":[],"model":"gpt-4o-mini","usage":{"prompt_tokens":206,"completion_tokens":231,"total_tokens":437}}
```

## Prompt Comparison (Based on Actual Outputs)

### /summarize
- Variant A returned a single paragraph with full context and smooth narrative flow.
- Variant B produced concise bullets with stable phrasing similar to the few-shot example.
- Variant C added a more action-oriented framing (e.g., “top funnel leak”) while staying bullet-based.

### /analyze-sentiment
- Variant A returned a longer single rationale without aspect breakdowns.
- Variant B produced structured aspect sentiment with short, example-like rationales.
- Variant C kept overall sentiment but emphasized conflicting signals in the rationale.

## Learning Summary (PromptingGuide.ai)

The Prompt Engineering Guide explains that prompt quality depends on how much information is provided and how well the prompt is crafted, including instruction, context, inputs, and examples. It shows that adding explicit instructions (e.g., “complete the sentence”) improves alignment compared to a bare prompt, underscoring why our API prompts include role, task, and JSON output format for predictable responses. It also notes that chat models can use `system`, `user`, and `assistant` roles to shape behavior, which we leveraged to stabilize outputs and enforce structure.

In the Prompting Techniques section, the guide frames prompt engineering as a way to improve reliability and performance on more complex tasks than basic prompting. It highlights techniques like zero-shot and few-shot prompting as foundational formats and then introduces advanced methods to handle more complex workflows. This aligns with our approach of testing multiple prompt variants per endpoint to trade off verbosity, structure, and diagnostic detail while keeping output formats stable for the API.
