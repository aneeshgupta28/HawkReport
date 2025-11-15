from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class newState(TypedDict):
    url: str
    content: str
    summary: str
    topics: list[str]


graph = StateGraph(newState)

graph.add_node(START, filter_relevant_news)

graph.add_node(filter_relevant_news, get_article_content)

graph.add_node(get_article_content, summarize_article)




