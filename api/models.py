"""Pydantic models for API request and response schemas."""

from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict


# Request models
class AnalyzeRequest(BaseModel):
    image_url: HttpUrl


class EditRequest(BaseModel):
    image_url: HttpUrl
    output_dir: Optional[str] = "output"


class ImageEditRequest(BaseModel):
    file_hash: str


# Response models
class AnalyzeResponse(BaseModel):
    analysis: str


class EditResponse(BaseModel):
    results: Dict[str, str]


class GeneratedImage(BaseModel):
    title: str
    image_path: str
    text_response: Optional[str] = None
    enhancements: Optional[Dict] = None
    metrics: Optional[Dict] = None


class ImageEditResponse(BaseModel):
    success: bool
    images: Optional[list[GeneratedImage]] = None
    error: Optional[str] = None


class AnalysisHistoryResponse(BaseModel):
    id: int
    filename: str
    analysis_text: str
    created_at: str
    exif_data: Optional[Dict[str, str]] = None
