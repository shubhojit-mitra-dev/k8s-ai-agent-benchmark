"""Test suite for mock and live LLM providers and pricing calculation."""

import asyncio
from backend.providers.mock_provider import MockModelProvider
from backend.providers import get_providers_for_arm
from backend.models.schema import PrimaryArm
from backend.config import BenchmarkSettings


def test_mock_provider_jev():
    settings = BenchmarkSettings()
    provider = MockModelProvider(model_id=settings.cf_jev_model, provider_name="Mock-Jev", settings=settings)
    res = asyncio.run(provider.call_jev_decision(
        incident_alert={"name": "CrashLoopBackOff"},
        accumulated_evidence=[],
        available_tools=["list_pods"],
    ))

    assert res.status_code == 200
    assert res.jev_decision is not None
    assert res.jev_decision.next_step != ""
    assert 0.0 <= res.jev_decision.confidence <= 1.0
    assert res.monotonic_latency_ms >= 5


def test_mock_provider_sonnet():
    settings = BenchmarkSettings()
    provider = MockModelProvider(model_id=settings.cf_sonnet_model, provider_name="Mock-Sonnet", settings=settings)
    res = asyncio.run(provider.call_sonnet_investigation(
        system_prompt="You are a k8s SRE agent",
        messages=[{"role": "user", "content": "K8S-001 alert context"}],
        tools=[],
    ))

    assert res.status_code == 200
    assert res.tool_call is not None
    assert res.estimated_cost_usd > 0.0


def test_provider_factory_mock():
    settings = BenchmarkSettings()
    sonnet_p, jev_p = get_providers_for_arm(PrimaryArm.CF_JEV_SONNET, settings=settings, force_mock=True)
    assert sonnet_p is not None
    assert jev_p is not None

    sonnet_p2, jev_p_none = get_providers_for_arm(PrimaryArm.CF_SONNET, settings=settings, force_mock=True)
    assert sonnet_p2 is not None
    assert jev_p_none is None
