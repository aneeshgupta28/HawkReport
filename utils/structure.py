from pydantic import BaseModel, Field
from typing import Literal, List


class Relevancy(BaseModel):
    relevance: Literal['high', 'medium', 'low'] = Field(..., description="how relevant is the article based on the provided rubrics")
    reason: str = Field(..., description="a brief explanation of why the article was rated this way")
    url: str = Field(..., description="the url of the article that is fetched from the rss")
    score: float = Field(..., description="the computed score based on the rubrics, rounded to 2 decimals")

class RelevancyList(BaseModel):
    items: List[Relevancy]

class isUpdate(BaseModel):
    is_update: Literal['UPDATE', 'DUPLICATE'] = Field(..., description="whether the article is an update to a previous story or a new story")