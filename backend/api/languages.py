"""
Language Registry & Capability Discovery API for TRANSLARA.
Fetches dynamically from MSSQL database with fallback to ML engine registry.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Language
from backend.database.session import get_db
from backend.ml_engine.languages import (
    get_all_languages,
    get_capabilities_matrix,
    get_grouped_languages,
)
from backend.schemas import CapabilitiesResponse, LanguageDetail, LanguagesResponse

router = APIRouter(prefix="/api", tags=["Languages"])


@router.get("/languages", response_model=LanguagesResponse)
async def list_languages(db: Session = Depends(get_db)):
    """
    Return list of all registered Indian languages grouped by geographical region.
    Retrieved from the primary MSSQL database with registry fallback.
    """
    try:
        db_languages = db.query(Language).filter(Language.is_active == True).all()
        if db_languages:
            # Map code -> static capability flags
            static_lookup = {l.code: l for l in get_all_languages()}
            details = [
                LanguageDetail(
                    code=lang.code,
                    name=lang.name,
                    native_name=lang.native_name,
                    region=lang.region,
                    script=lang.script,
                    asr_supported=static_lookup[lang.code].asr_supported if lang.code in static_lookup else True,
                    translation_supported=static_lookup[lang.code].translation_supported if lang.code in static_lookup else True,
                    tts_supported=static_lookup[lang.code].tts_supported if lang.code in static_lookup else True,
                    offline_supported=static_lookup[lang.code].offline_supported if lang.code in static_lookup else True,
                )
                for lang in db_languages
            ]

            # Build grouped dictionary by region
            grouped_details: dict[str, list[LanguageDetail]] = {}
            for item in details:
                region_name = item.region
                if region_name not in grouped_details:
                    grouped_details[region_name] = []
                grouped_details[region_name].append(item)

            return LanguagesResponse(languages=details, grouped=grouped_details)
    except Exception:
        pass

    # Fallback to static registry
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
    grouped_details = {}
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
