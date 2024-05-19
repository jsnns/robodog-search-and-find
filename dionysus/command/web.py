from concurrent.futures import ThreadPoolExecutor, as_completed
from re import search
from typing import List

from langchain.utilities import WikipediaAPIWrapper
from tqdm import tqdm

from dionysus.argument.base import Argument
from dionysus.argument_type.primative import Boolean, Number, String
from dionysus.command.base import Command
from dionysus.command.observation import Observation, ObservedError
from dionysus.command.thought_chain import Step, StepResult, StepStatus, ThoughtChain
from common.ai.llm.ask_llms import pick_most_relevant_with_gpt4, summarize_this
from vendor.gitbook import search_pluto_knowledgebase
from vendor.serpapi import OrganicResult, search_google


class PlutoKnowledgeBaseSearch(Command):
    action_name_for_end_user = "Pluto Knowledge Base"
    arguments: list[Argument] = [Argument("query", String())]

    def run(self, args, chat_log):
        query = args.get("query")

        results = search_pluto_knowledgebase(query, k=3)

        results = "\n\n".join(results) if results else "No results found"

        yield Observation(
            query=f"Search Pluto customer support Knowledge Base for {query}",
            result=results,
            user_title=f'Reading about "{query}"',
            user_explanation=f'Searching Knowledge Base for "{query}"\n\n{results}',
        )


class Wikipedia(Command):
    action_name_for_end_user = "Wikipedia"
    arguments: list[Argument] = [
        Argument("topic", String()),
        Argument("query", String(), required=False),
    ]

    def run(self, args, chat_log):
        topic = args.get("topic") or ""
        query = args.get("query") or ""

        chain = ThoughtChain.new(f"Read Wikipedia articles about {topic} {query}")
        chain.add_step(Step.search("Searching Wikipedia"))
        yield chain

        wikipedia = WikipediaAPIWrapper()
        result: str = wikipedia.run(f"{topic} {query}".strip())

        if not result:
            yield Observation(
                query=f"Get Wikipedia article for {topic} {query}",
                result="No Wikipedia article found",
                hide_from_user=True,
            )
            chain.finalize("No Wikipedia article found")
            yield chain
            return

        yield Observation(
            query=f"Get Wikipedia article for {topic} {query}",
            result=result,
            hide_from_user=True,
        )

        chain.add_step(Step.read(f"Read Wikipedia article about {topic} {query}"))
        chain.finalize()
        yield chain


def get_all_organic_results(news: List[OrganicResult]) -> List[str]:
    with ThreadPoolExecutor() as executor:
        future_to_content = {executor.submit(article.content): article for article in news}
        content = []

        for future in tqdm(
            as_completed(future_to_content),
            total=len(future_to_content),
            desc="Downloading news content",
        ):
            article = future_to_content[future]
            try:
                content_result = future.result()
            except Exception as exc:
                print("%r generated an exception: %s" % (article, exc))
            else:
                if content_result:
                    content.append(f"{article.title}: {content_result}")

    return content


class SearchGoogle(Command):
    """Get data that the DSL doesn't support."""

    action_name_for_end_user = "Web search"
    arguments: list[Argument] = [
        Argument("search_term", String()),
        Argument("summary_focus", String(), required=False),
    ]

    def run(self, args, chat_log):
        query = args.get("search_term")
        summary_focus = args.get("summary_focus")

        results = search_google(query)

        content: List[str] = get_all_organic_results(results.organic_results)

        if results.answer_box:
            content.append(f"{results.answer_box.title}: {results.answer_box.snippet}")

        if not content:
            yield ObservedError(
                attempted_action=f"Get news for {query}",
                error="No news found",
            )
            return

        for result in results.organic_results:
            yield result.as_source()

        yield Observation.new(summarize_this("\n\n".join(content), focus=summary_focus))


def test():
    for result in SearchGoogle().run({"search_term": "what's going on in the red sea"}, None):
        if isinstance(result, Observation):
            print(result.summary_for_ai())
