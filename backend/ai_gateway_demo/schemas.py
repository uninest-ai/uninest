"""
Pydantic contracts shared between the gateway and the microservice.

These schemas ARE the type contract (a shared `schemas/` layer):
both sides validate/serialize with them, so neither can drift from the other.
"""
from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to embed")


class EmbedResponse(BaseModel):
    model: str
    dim: int
    embedding: list[float]


class IndexRequest(BaseModel):
    property_id: int
    text: str = Field(..., min_length=1)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=50)


class SearchHit(BaseModel):
    property_id: int
    score: float


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
