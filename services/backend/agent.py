import json
import logging
from typing import Optional

from llm import LLMClient, LLMError, llm_client
from scraper import ScraperClient, ScraperError, scraper_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agent")


DECISION_PROMPT = """You are a helpful assistant that decides whether a question requires current information from the web.

Analyze the following question and determine if it needs web search to provide an accurate, up-to-date answer.

Questions that typically NEED web search:
- Current events, news, or recent developments
- Real-time data (prices, weather, stock prices)
- Information that changes frequently
- Questions about specific recent dates or events
- Questions about current versions of software, products, etc.

Questions that typically DON'T need web search:
- General knowledge, concepts, or explanations
- Historical facts
- How-to guides for established processes
- Mathematical or logical problems
- Definitions or explanations of well-known topics

Question: {question}

Respond with ONLY a JSON object (no markdown, no explanation):
{{"needs_search": true/false, "reason": "brief explanation"}}"""

KEYWORD_PROMPT = """Extract the best search keywords from this question to find relevant information on Google.

Question: {question}

Respond with ONLY a JSON object (no markdown, no explanation):
{{"keywords": "optimized search query"}}"""

ANSWER_WITH_SEARCH_PROMPT = """You are a helpful research assistant. Answer the user's question using the search results provided.

Question: {question}

Search Results:
{search_results}

Instructions:
- Provide a comprehensive answer based on the search results
- If the search results don't contain relevant information, say so
- Cite sources when possible by mentioning the source title
- Be concise but thorough"""

ANSWER_DIRECT_PROMPT = """You are a helpful assistant. Answer the following question based on your knowledge.

Question: {question}

Provide a clear, accurate, and helpful response."""


class ResearchAgent:
    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        scraper: Optional[ScraperClient] = None,
    ):
        self.llm = llm or llm_client
        self.scraper = scraper or scraper_client

    async def _needs_web_search(self, question: str) -> tuple[bool, str]:
        """Determine if the question needs web search."""
        logger.info("Deciding if web search is needed...")

        try:
            response = await self.llm.prompt(
                DECISION_PROMPT.format(question=question),
                temperature=0.1,
            )

            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0]

            data = json.loads(response)
            needs_search = data.get("needs_search", False)
            reason = data.get("reason", "")

            logger.info(f"Decision: needs_search={needs_search}, reason={reason}")
            return needs_search, reason

        except (json.JSONDecodeError, LLMError) as e:
            logger.warning(f"Failed to parse decision, defaulting to no search: {e}")
            return False, "Failed to determine, using direct answer"

    async def _extract_keywords(self, question: str) -> str:
        """Extract search keywords from the question."""
        logger.info("Extracting search keywords...")

        try:
            response = await self.llm.prompt(
                KEYWORD_PROMPT.format(question=question),
                temperature=0.1,
            )

            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0]

            data = json.loads(response)
            keywords = data.get("keywords", question)

            logger.info(f"Search keywords: {keywords}")
            return keywords

        except (json.JSONDecodeError, LLMError) as e:
            logger.warning(f"Failed to extract keywords, using original question: {e}")
            return question

    async def _search_web(self, keywords: str, num_results: int = 5) -> list[dict]:
        """Perform web search and return results."""
        logger.info(f"Searching web for: {keywords}")

        try:
            results = await self.scraper.search_as_dict(keywords, num_results)
            logger.info(f"Found {len(results)} search results")
            return results

        except ScraperError as e:
            logger.error(f"Web search failed: {e}")
            return []

    async def _answer_with_results(self, question: str, search_results: list[dict]) -> str:
        """Generate answer using search results."""
        logger.info("Generating answer from search results...")

        # Format search results for the prompt
        formatted_results = ""
        for i, result in enumerate(search_results, 1):
            formatted_results += f"\n{i}. {result['title']}\n"
            formatted_results += f"   URL: {result['url']}\n"
            formatted_results += f"   {result['description']}\n"

        response = await self.llm.prompt(
            ANSWER_WITH_SEARCH_PROMPT.format(
                question=question,
                search_results=formatted_results,
            ),
            temperature=0.7,
        )

        return response

    async def _answer_direct(self, question: str) -> str:
        """Generate answer directly from LLM knowledge."""
        logger.info("Generating direct answer from LLM knowledge...")

        response = await self.llm.prompt(
            ANSWER_DIRECT_PROMPT.format(question=question),
            temperature=0.7,
        )

        return response

    async def answer(self, question: str, use_web_search: bool = True) -> dict:
        """
        Answer a question, optionally using web search if needed.

        Args:
            question: The user's question.
            use_web_search: If False, skip web search entirely and answer directly.

        Returns:
            Dict with 'answer', 'used_search', 'search_results', and 'reason'.
        """
        logger.info(f"Processing question: {question}")

        result = {
            "question": question,
            "answer": "",
            "used_search": False,
            "search_results": [],
            "reason": "",
        }

        try:
            # Skip web search decision if disabled
            if not use_web_search:
                logger.info("Web search disabled, answering directly")
                result["reason"] = "Web search disabled"
                result["answer"] = await self._answer_direct(question)
                return result

            # Decide if web search is needed
            needs_search, reason = await self._needs_web_search(question)
            result["reason"] = reason

            if needs_search:
                # Extract keywords and search
                keywords = await self._extract_keywords(question)
                search_results = await self._search_web(keywords)
                result["search_results"] = search_results
                result["used_search"] = True

                if search_results:
                    result["answer"] = await self._answer_with_results(question, search_results)
                else:
                    logger.warning("No search results, falling back to direct answer")
                    result["answer"] = await self._answer_direct(question)
            else:
                result["answer"] = await self._answer_direct(question)

        except LLMError as e:
            logger.error(f"LLM error: {e}")
            result["answer"] = f"Sorry, I encountered an error: {e.message}"

        logger.info("Question processing complete")
        return result


research_agent = ResearchAgent()
