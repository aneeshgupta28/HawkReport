from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv
from datetime import datetime
import os, news
from news import fetch_rss
load_dotenv()


class Relevancy(BaseModel):
    relevance: Literal['high', 'medium', 'low'] = Field(..., description="how relevant is the article based on the provided rubrics")
    reason: str = Field(..., description="a brief explanation of why the article was rated this way")
    url: str = Field(..., description="the url of the article that is fetched from the rss")
    score: float = Field(..., description="the computed score based on the rubrics, rounded to 2 decimals")

current_time = datetime.now().isoformat()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)

llm_structured = llm.with_structured_output(Relevancy)

prompt = PromptTemplate.from_template("""
You are an expert news journalist. Given the following rss feed to you, decide which articles are the most important/relevant to be posted on your twitter feed based on the following rubrics:\n
rubrics: {rubrics}\n
rss_feed: {rss_feed}""")

rubrics = """
CURRENT_TIME_ISO: <{current_time}>
MAX_SELECT: 2

RUBRIC SUMMARY (compute sub-scores in [0.00-1.00], round to 2 decimals):
- Novelty (0.30): how new is the fact; crisis keywords => novelty >= 0.90 bias.
- Impact (0.25): how many people/markets/policies are affected.
- Source Credibility (0.20): map host → 0.00–1.00 (use provided source map if available).
- Freshness (0.15): minutes since published (<=15 => 1.00; <=60 => 0.70; <=180 => 0.30; >180 or missing => 0.00).
- Audience Relevance (0.10): section-specific relevance to an India-first, tech-savvy audience.

Combine:
score = 0.30*novelty + 0.25*impact + 0.20*credibility + 0.15*freshness + 0.10*audience_relevance

Mapping:
- score >= 0.70 -> relevancy = "high", selected = true
- 0.45 <= score < 0.70 -> relevancy = "medium", selected = true only if slots remain after high items
- score < 0.45 -> relevancy = "low", selected = false

Selection policy:
- Pick up to MAX_SELECT per section: fill with high items (by score) then medium if slots remain.
- Avoid selecting >1 item from same host unless unavoidable; only allow second if its score >= top alternative + 0.05.
- Do NOT invent facts — key_facts must be short bullet phrases extracted from title/snippet only.
"""

test1 = llm_structured.invoke(
    prompt.format_prompt(
        rubrics=rubrics.format(current_time=current_time),
        rss_feed=fetch_rss(news.rss_india[0])
))

print(test1)