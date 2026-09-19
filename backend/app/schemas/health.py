"""
Pydantic schemas for Backend & Model Health APIs.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ModelHealthStatus(BaseModel):
    status: str = Field(..., description="READY, UNAVAILABLE, or FAILED")
    task: str
    artifact_path: str
    framework: str
    last_error: str = None


class ModelsHealthResponse(BaseModel):
    status: str = Field(..., description="Overall health: healthy or degraded")
    models: Dict[str, str] = Field(..., description="Map of model key to status (READY / UNAVAILABLE)")
    details: Dict[str, ModelHealthStatus] = Field(default_factory=dict)
