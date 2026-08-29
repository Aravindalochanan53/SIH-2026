"""
Language Registry & Capability Discovery API for TRANSLARA.
"""
from fastapi import APIRouter
from backend.config import settings
from backend.ml_engine.languages import (
    get_all_languages,
    get_capabilities_matrix,
    get_grouped_languages,
)
from backend.schemas import CapabilitiesResponse, LanguageDetail, LanguagesResponse

router = APIRouter(prefix="/api", tags=["Languages"])


@router.get("/languages", response_model=LanguagesResponse)
async def list_languages():
    """
    Return list of all registered Indian languages grouped by geographical region.
    Used by frontend and browser extension to dynamically populate language selectors.
    """
    all_langs = get_all_languages()
    details = [
        LanguageDetail(
            code=l.code,
            name=l.name,
            native_name=l.native_name,
            region=l.region,
            script=l.script,
            asr_supported=l.asr_supported,
            translation_supported=l.translation_supported,
            tts_supported=l.tts_supported,
            offline_supported=l.offline_supported,
        )
        for l in all_langs
    ]

    grouped_raw = get_grouped_languages()
    grouped_details: dict[str, list[LanguageDetail]] = {}
    for region_name, items in grouped_raw.items():
        grouped_details[region_name] = [
            LanguageDetail(
                code=it["code"],
                name=it["name"],
                native_name=it["native_name"],
                region=it["region"],
                script=it["script"],
                asr_supported=it["asr_supported"],
                translation_supported=it["translation_supported"],
                tts_supported=it["tts_supported"],
                offline_supported=it["offline_supported"],
            )
            for it in items
        ]

    return LanguagesResponse(languages=details, grouped=grouped_details)


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    """
    Return active model backend capability matrix across all supported languages.
    """
    matrix = get_capabilities_matrix(settings.nmt_backend)
    return CapabilitiesResponse(
        active_asr_backend=settings.asr_backend,
        active_nmt_backend=settings.nmt_backend,
        active_tts_backend=settings.tts_backend,
        mock_mode=settings.mock_mode,
        languages=matrix,
    )
