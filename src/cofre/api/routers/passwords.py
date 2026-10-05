"""Public endpoints: they touch no user data (RF-14, RF-15)."""

from fastapi import APIRouter

from cofre.api.schemas.passwords import (
    GenerateRequest,
    GenerateResponse,
    StrengthRequest,
    StrengthResponse,
)
from cofre.services.passwords import PasswordGenerator, StrengthEstimator

router = APIRouter(prefix="/api/v1/passwords", tags=["passwords"])

_generator = PasswordGenerator()
_estimator = StrengthEstimator()


@router.post("/generate", summary="Gera uma senha aleatória.")
def generate(payload: GenerateRequest) -> GenerateResponse:
    password = _generator.generate(**payload.model_dump())
    return GenerateResponse(password=password)


@router.post("/strength", summary="Avalia a força de uma senha.")
def strength(payload: StrengthRequest) -> StrengthResponse:
    result = _estimator.estimate(payload.password.get_secret_value())
    return StrengthResponse(
        score=result.score,
        weak=result.weak,
        crack_time_seconds=result.crack_time_seconds,
        crack_time_display=result.crack_time_display,
        suggestions=result.suggestions,
    )
