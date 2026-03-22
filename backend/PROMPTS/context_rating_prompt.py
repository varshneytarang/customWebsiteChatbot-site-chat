from langchain.prompts import PromptTemplate


context_rating_prompt = """
You are a strict context relevance evaluator for a retrieval-based QA system.

Task:
Given a user question and retrieved webpage context, rate how relevant and sufficient the context is for answering the question.

Scoring rubric (0-100):
- 0-20: Context is unrelated or unusable.
- 21-40: Slight overlap, but key facts are missing.
- 41-60: Partially relevant; enough for a weak/partial answer.
- 61-80: Mostly relevant; enough for a good answer with minor gaps.
- 81-100: Highly relevant and sufficient for a strong answer.

Evaluation rules:
- Judge only from provided context and question.
- Do not assume hidden knowledge.
- Penalize missing critical facts.
- Penalize contradictions or noise in context.
- Be conservative: do not over-score weak matches.

Output rules (MUST follow exactly):
- Return valid JSON only.
- No markdown, no extra text, no code fences.
- Use this exact schema:
{{
  "relevance_score": <integer 0-100>,
  "relevance_label": "low" | "medium" | "high",
  "reason": "one concise sentence"
}}

Label mapping:
- low: 0-40
- medium: 41-70
- high: 71-100

Inputs:
Question:
{question}

Context:
{context}
"""


context_rating_prompt_template = PromptTemplate(
  input_variables=["question", "context"],
  template=context_rating_prompt,
)
