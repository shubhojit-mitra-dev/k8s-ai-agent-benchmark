"""
Provider factory and adapter registration module.
"""

from typing import Optional, Tuple
from backend.config import BenchmarkSettings
from backend.models.schema import PrimaryArm
from backend.providers.base import BaseProvider, ProviderResponse
from backend.providers.cloudflare import CloudflareSonnetProvider, CloudflareJevProvider
from backend.providers.openrouter import OpenRouterSonnetProvider, OpenRouterJevProvider
from backend.providers.mock_provider import MockModelProvider

__all__ = [
    "BaseProvider",
    "ProviderResponse",
    "CloudflareSonnetProvider",
    "CloudflareJevProvider",
    "OpenRouterSonnetProvider",
    "OpenRouterJevProvider",
    "MockModelProvider",
    "get_providers_for_arm",
]


def get_providers_for_arm(
    arm: PrimaryArm | str, settings: BenchmarkSettings, force_mock: bool = False
) -> Tuple[BaseProvider, Optional[BaseProvider]]:
    """
    Returns (sonnet_provider, jev_provider).
    If credentials are missing or force_mock is True, returns high-fidelity mock providers.
    """
    arm_str = arm.value if isinstance(arm, PrimaryArm) else str(arm)

    if force_mock:
        sonnet_prov = MockModelProvider(
            model_id=settings.cf_sonnet_model, provider_name="Mock-Sonnet", settings=settings
        )
        jev_prov = (
            MockModelProvider(
                model_id=settings.cf_jev_model, provider_name="Mock-Jev", settings=settings
            )
            if "JEV" in arm_str
            else None
        )
        return sonnet_prov, jev_prov

    if arm_str == PrimaryArm.CF_SONNET.value:
        if settings.is_cf_configured():
            return CloudflareSonnetProvider(model_id=settings.cf_sonnet_model, settings=settings), None
        return MockModelProvider(model_id=settings.cf_sonnet_model, provider_name="CF-Sonnet-Mock", settings=settings), None

    elif arm_str == PrimaryArm.CF_JEV_SONNET.value:
        if settings.is_cf_configured():
            sonnet = CloudflareSonnetProvider(model_id=settings.cf_sonnet_model, settings=settings)
            jev = CloudflareJevProvider(model_id=settings.cf_jev_model, settings=settings)
            return sonnet, jev
        sonnet = MockModelProvider(model_id=settings.cf_sonnet_model, provider_name="CF-Sonnet-Mock", settings=settings)
        jev = MockModelProvider(model_id=settings.cf_jev_model, provider_name="CF-Jev-Mock", settings=settings)
        return sonnet, jev

    elif arm_str == PrimaryArm.OR_SONNET.value:
        if settings.is_or_configured():
            return OpenRouterSonnetProvider(model_id=settings.or_sonnet_model, settings=settings), None
        return MockModelProvider(model_id=settings.or_sonnet_model, provider_name="OR-Sonnet-Mock", settings=settings), None

    elif arm_str == PrimaryArm.OR_JEV_SONNET.value:
        if settings.is_or_configured():
            sonnet = OpenRouterSonnetProvider(model_id=settings.or_sonnet_model, settings=settings)
            jev = OpenRouterJevProvider(model_id=settings.or_jev_model, settings=settings)
            return sonnet, jev
        sonnet = MockModelProvider(model_id=settings.or_sonnet_model, provider_name="OR-Sonnet-Mock", settings=settings)
        jev = MockModelProvider(model_id=settings.or_jev_model, provider_name="OR-Jev-Mock", settings=settings)
        return sonnet, jev

    # Default fallback
    return (
        MockModelProvider(model_id=settings.cf_sonnet_model, provider_name="Mock-Sonnet", settings=settings),
        MockModelProvider(model_id=settings.cf_jev_model, provider_name="Mock-Jev", settings=settings) if "JEV" in arm_str else None,
    )
