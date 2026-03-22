import os

from tavily import TavilyClient


def _get_tavily_client():
	api_key = os.getenv("TAVILY_API_KEY")
	return TavilyClient(api_key=api_key) if api_key else None


def get_web_context(question, max_results=5):
	client = _get_tavily_client()
	if client is None:
		return {
			"snippets_text": "",
			"sources": [],
			"used_web_fallback": False,
			"reason": "missing_tavily_api_key",
		}

	search_response = client.search(
		query=question,
		search_depth="advanced",
		max_results=max_results,
		include_answer=True,
	)

	results = search_response.get("results", [])
	snippets = []
	sources = []

	for item in results[:max_results]:
		title = item.get("title", "Untitled source")
		url = item.get("url", "")
		if content := item.get("content", ""):
			snippets.append(f"- {title}: {content}")
		sources.append({"title": title, "url": url})

	tavily_answer = search_response.get("answer", "")

	blocks = []
	if tavily_answer:
		blocks.append(f"- Tavily summary: {tavily_answer}")
	if snippets:
		blocks.append("\n".join(snippets))

	snippets_text = "\n".join(blocks).strip()

	return {
		"snippets_text": snippets_text,
		"sources": sources,
		"used_web_fallback": bool(snippets_text),
		"reason": "low_context_relevance",
	}
