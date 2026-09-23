"""
Kubernetes simulated resource primitives and domain models.
Provides structural fidelity for realistic kubectl diagnostic generation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class K8sContainerState(BaseModel):
    state: str = "running"  # running, waiting, terminated
    reason: Optional[str] = None  # OOMKilled, CrashLoopBackOff, ImagePullBackOff, Error
    exit_code: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class K8sContainer(BaseModel):
    name: str
    image: str
    memory_limit: str = "512Mi"
    memory_request: str = "256Mi"
    cpu_limit: str = "500m"
    cpu_request: str = "100m"
    current_state: K8sContainerState = Field(default_factory=K8sContainerState)
    last_state: Optional[K8sContainerState] = None
    ready: bool = True
    restart_count: int = 0
    readiness_probe_path: Optional[str] = None
    readiness_probe_status: bool = True
    liveness_probe_path: Optional[str] = None
    liveness_probe_status: bool = True


class K8sPod(BaseModel):
    name: str
    namespace: str
    node_name: str = "node-1"
    ip: str = "10.244.1.15"
    phase: str = "Running"  # Running, Pending, Failed, Succeeded
    status_summary: str = "Running"
    ready_summary: str = "1/1"
    restarts: int = 0
    age: str = "24m"
    labels: Dict[str, str] = Field(default_factory=dict)
    containers: List[K8sContainer] = Field(default_factory=list)
    qos_class: str = "Burstable"  # Guaranteed, Burstable, BestEffort
    priority: int = 0
    logs: List[str] = Field(default_factory=list)
    previous_logs: List[str] = Field(default_factory=list)
    cpu_usage_millicores: int = 45
    memory_usage_mb: int = 210


class K8sNode(BaseModel):
    name: str
    status: str = "Ready"  # Ready, NotReady
    ready_condition: bool = True
    disk_pressure: bool = False
    memory_pressure: bool = False
    pid_pressure: bool = False
    unschedulable: bool = False  # cordoned
    capacity_cpu: str = "4000m"
    capacity_memory: str = "16Gi"
    capacity_storage: str = "100Gi"
    allocatable_cpu: str = "3800m"
    allocatable_memory: str = "15Gi"
    allocatable_storage: str = "90Gi"
    usage_cpu_millicores: int = 1200
    usage_memory_mb: int = 5400
    usage_disk_percent: int = 42
    kubelet_status: str = "Active (running)"


class K8sDeployment(BaseModel):
    name: str
    namespace: str
    replicas: int = 3
    ready_replicas: int = 3
    updated_replicas: int = 3
    available_replicas: int = 3
    selector_labels: Dict[str, str] = Field(default_factory=dict)
    template_labels: Dict[str, str] = Field(default_factory=dict)
    image: str = "registry.internal/api:v1.2.0"
    revision: int = 2
    previous_revision_image: Optional[str] = "registry.internal/api:v1.1.9"
    rollout_status: str = "deployment successfully rolled out"


class K8sReplicaSet(BaseModel):
    name: str
    namespace: str
    deployment_name: str
    revision: int
    replicas: int
    ready_replicas: int
    image: str


class K8sService(BaseModel):
    name: str
    namespace: str
    service_type: str = "ClusterIP"
    cluster_ip: str = "10.96.12.44"
    ports: List[Dict[str, Any]] = Field(default_factory=list)
    selector: Dict[str, str] = Field(default_factory=dict)


class K8sEndpoint(BaseModel):
    name: str
    namespace: str
    subsets: List[Dict[str, Any]] = Field(default_factory=list)


class K8sIngress(BaseModel):
    name: str
    namespace: str
    hosts: List[str] = Field(default_factory=list)
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    tls_configured: bool = True


class K8sConfigMap(BaseModel):
    name: str
    namespace: str
    data_keys: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class K8sSecretMetadata(BaseModel):
    name: str
    namespace: str
    type_name: str = "Opaque"
    data_keys: List[str] = Field(default_factory=list)


class K8sNetworkPolicy(BaseModel):
    name: str
    namespace: str
    pod_selector: Dict[str, str] = Field(default_factory=dict)
    ingress_rules: List[Dict[str, Any]] = Field(default_factory=list)
    egress_rules: List[Dict[str, Any]] = Field(default_factory=list)


class K8sResourceQuota(BaseModel):
    name: str
    namespace: str
    hard: Dict[str, str] = Field(default_factory=dict)
    used: Dict[str, str] = Field(default_factory=dict)


class K8sLimitRange(BaseModel):
    name: str
    namespace: str
    limits: List[Dict[str, Any]] = Field(default_factory=list)


class K8sHPA(BaseModel):
    name: str
    namespace: str
    reference_name: str
    min_replicas: int = 2
    max_replicas: int = 10
    current_replicas: int = 3
    target_cpu_percent: int = 75
    current_cpu_percent: int = 88


class K8sPDB(BaseModel):
    name: str
    namespace: str
    min_available: Optional[int] = 1
    max_unavailable: Optional[int] = None
    current_healthy: int = 3
    desired_healthy: int = 3
    disruptions_allowed: int = 2


class K8sEvent(BaseModel):
    timestamp_str: str = "12m"
    event_type: str = "Normal"  # Normal, Warning
    reason: str = "Scheduled"
    involved_object: str = "Pod/payment-api-xyz"
    message: str = "Successfully assigned payments/payment-api-xyz to node-1"


class KafkaState(BaseModel):
    consumer_group: str = "payments-processor"
    topic: str = "orders-stream"
    partition_count: int = 8
    total_lag: int = 120
    consumer_count: int = 4
    processing_latency_p99_ms: float = 38.0
    cpu_throttled: bool = False


class RedisState(BaseModel):
    service_name: str = "redis-primary"
    status: str = "PONG"
    connected_clients: int = 42
    max_clients: int = 10000
    used_memory_human: str = "128M"
    max_memory_human: str = "2Gi"
    is_responsive: bool = True
    network_partitioned_nodes: List[str] = Field(default_factory=list)


class PostgresState(BaseModel):
    service_name: str = "postgres-cluster"
    status: str = "healthy"
    active_connections: int = 18
    max_connections: int = 200
    p95_query_time_ms: float = 4.2
    lock_wait_count: int = 0


class DNSState(BaseModel):
    coredns_healthy: bool = True
    upstream_responsive: bool = True
    failing_domains: List[str] = Field(default_factory=list)


class ClusterState(BaseModel):
    """Encapsulates the complete simulated state of a cluster."""
    name: str = "k8s-prod-cluster"
    nodes: Dict[str, K8sNode] = Field(default_factory=dict)
    namespaces: List[str] = Field(
        default_factory=lambda: ["default", "kube-system", "payments", "orders", "frontend"]
    )
    pods: Dict[str, K8sPod] = Field(default_factory=dict)
    deployments: Dict[str, K8sDeployment] = Field(default_factory=dict)
    replicasets: Dict[str, K8sReplicaSet] = Field(default_factory=dict)
    services: Dict[str, K8sService] = Field(default_factory=dict)
    endpoints: Dict[str, K8sEndpoint] = Field(default_factory=dict)
    ingresses: Dict[str, K8sIngress] = Field(default_factory=dict)
    configmaps: Dict[str, K8sConfigMap] = Field(default_factory=dict)
    secrets: Dict[str, K8sSecretMetadata] = Field(default_factory=dict)
    network_policies: Dict[str, K8sNetworkPolicy] = Field(default_factory=dict)
    resource_quotas: Dict[str, K8sResourceQuota] = Field(default_factory=dict)
    limit_ranges: Dict[str, K8sLimitRange] = Field(default_factory=dict)
    hpas: Dict[str, K8sHPA] = Field(default_factory=dict)
    pdbs: Dict[str, K8sPDB] = Field(default_factory=dict)
    events: List[K8sEvent] = Field(default_factory=list)
    kafka: Optional[KafkaState] = None
    redis: Optional[RedisState] = None
    postgres: Optional[PostgresState] = None
    dns: Optional[DNSState] = None
    recent_changes: List[str] = Field(default_factory=list)

    def calculate_sha256(self) -> str:
        dump = self.model_dump_json(exclude={"events"})
        return hashlib.sha256(dump.encode("utf-8")).hexdigest()
