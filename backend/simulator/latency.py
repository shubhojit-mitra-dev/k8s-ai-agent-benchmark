"""
Deterministic tool latency simulation module.
Ensures tool latency is completely identical and controlled across all experiment arms.
"""

from __future__ import annotations

from typing import Dict

# Deterministic tool latency values in milliseconds as required by specification
TOOL_LATENCY_TABLE_MS: Dict[str, float] = {
    # Simple metadata queries (15ms)
    "get_cluster_state": 60.0,  # cluster-wide query
    "get_nodes": 60.0,
    "get_node": 15.0,
    "get_node_metrics": 20.0,
    "list_pods": 60.0,
    "get_pod": 15.0,
    "describe_pod": 25.0,
    "get_pod_metrics": 20.0,
    "get_pod_logs": 30.0,
    "get_previous_pod_logs": 30.0,
    "get_events": 60.0,
    "get_namespace_events": 30.0,
    "get_cluster_events": 60.0,
    "get_deployment": 15.0,
    "get_replicasets": 20.0,
    "get_rollout_status": 15.0,
    "get_rollout_history": 25.0,
    "get_service": 15.0,
    "get_endpoints": 15.0,
    "get_endpointslices": 15.0,
    "get_ingress": 15.0,
    "get_network_policies": 20.0,
    "get_hpa": 15.0,
    "get_pdb": 15.0,
    "get_resource_quota": 15.0,
    "get_limit_range": 15.0,
    "get_configmap_metadata": 15.0,
    "get_secret_metadata": 15.0,
    "dns_lookup": 45.0,
    "http_probe": 45.0,
    "tcp_probe": 45.0,
    "get_kubelet_status": 20.0,
    "get_application_metrics": 20.0,
    "get_kafka_consumer_group": 25.0,
    "get_kafka_partition_lag": 25.0,
    "get_redis_status": 20.0,
    "get_redis_metrics": 20.0,
    "get_database_health": 25.0,
    "get_recent_changes": 20.0,
    
    # State mutation tools (simulated action execution latency)
    "restart_pod": 75.0,
    "scale_deployment": 60.0,
    "rollback_deployment": 85.0,
    "adjust_resources": 50.0,
    "cordon_node": 40.0,
    "drain_node": 120.0,
    "delete_pod": 50.0,
    "restart_deployment": 90.0,
}

DEFAULT_QUERY_LATENCY_MS: float = 20.0


def get_deterministic_tool_latency(tool_name: str) -> float:
    """Returns exact deterministic latency for the specified tool in milliseconds."""
    return TOOL_LATENCY_TABLE_MS.get(tool_name, DEFAULT_QUERY_LATENCY_MS)
