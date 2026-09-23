"""
Kubernetes Scenario Definitions (K8S-001 through K8S-020).
Monotonically increasing difficulty ladder with realistic Kubernetes topologies,
events, logs, metrics, hidden causal truths, and decision graphs.
"""

from __future__ import annotations

from typing import Dict, List
from backend.models.k8s_resources import (
    ClusterState,
    K8sPod,
    K8sContainer,
    K8sContainerState,
    K8sNode,
    K8sDeployment,
    K8sReplicaSet,
    K8sService,
    K8sEndpoint,
    K8sIngress,
    K8sConfigMap,
    K8sSecretMetadata,
    K8sNetworkPolicy,
    K8sResourceQuota,
    K8sLimitRange,
    K8sHPA,
    K8sPDB,
    K8sEvent,
    KafkaState,
    RedisState,
    PostgresState,
    DNSState,
)
from backend.models.schema import ScenarioMetadata
from backend.scenarios.graphs import ScenarioDecisionGraph

def _base_nodes() -> Dict[str, K8sNode]:
    return {
        "node-1": K8sNode(name="node-1"),
        "node-2": K8sNode(name="node-2"),
        "node-3": K8sNode(name="node-3"),
    }

def get_all_scenarios() -> List[ScenarioMetadata]:
    scenarios = []

    # K8S-001: Level 1 - OOMKilled payment API
    scenarios.append(
        ScenarioMetadata(
            id="K8S-001",
            title="Payment API Pod Repeatedly OOMKilled",
            difficulty=1,
            category="Resource Exhaustion",
            initial_alert={
                "alert": "PaymentAPIAvailabilityLow",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "66%",
                "message": "1 of 3 replicas failing health checks in namespace payments."
            },
            hidden_root_cause="Container memory limit (512Mi) exceeded by memory leak under load; exit code 137.",
            hidden_secondary_effects=["readiness probe failure", "restarts increasing"],
            valid_investigation_paths=[
                ["list_pods", "describe_pod", "get_pod_metrics", "adjust_resources"],
                ["get_pod", "get_previous_pod_logs", "get_pod_metrics", "adjust_resources"]
            ],
            unsafe_actions=["delete_namespace", "drain_node", "cordon_node"],
            correct_resolution_conditions={"action": "adjust_resources", "target": "payments-api", "memory": 1024},
            ground_truth_rationale="Pod container was terminated with OOMKilled (code 137). Increasing memory limit resolves the crash loop.",
            expected_tool_sequences=[["list_pods", "describe_pod", "get_pod_metrics"]],
            allowed_alternative_paths=[["get_pod", "get_previous_pod_logs"]]
        )
    )

    # K8S-002: Level 2 - ImagePullBackOff
    scenarios.append(
        ScenarioMetadata(
            id="K8S-002",
            title="ImagePullBackOff Following Release",
            difficulty=2,
            category="Deployment Failure",
            initial_alert={
                "alert": "DeploymentRolloutStuck",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "50%",
                "message": "Deployment payments-api rollout is not progressing."
            },
            hidden_root_cause="Typo in container image tag (v1.2.0-rc99 instead of v1.2.0) causing ErrImagePull.",
            hidden_secondary_effects=["ImagePullBackOff status", "deployment replica unavailable"],
            valid_investigation_paths=[
                ["get_deployment", "describe_pod", "get_events", "rollback_deployment"],
                ["list_pods", "get_events", "rollback_deployment"]
            ],
            unsafe_actions=["drain_node", "cordon_node"],
            correct_resolution_conditions={"action": "rollback_deployment", "target": "payments-api"},
            ground_truth_rationale="New pod fails with ErrImagePull due to non-existent image tag. Rolling back resolves the stuck deployment.",
            expected_tool_sequences=[["get_deployment", "describe_pod", "get_events"]],
            allowed_alternative_paths=[["list_pods", "get_events"]]
        )
    )

    # K8S-003: Level 3 - Missing ConfigMap Key CrashLoopBackOff
    scenarios.append(
        ScenarioMetadata(
            id="K8S-003",
            title="CrashLoopBackOff Caused by Missing ConfigMap Key",
            difficulty=3,
            category="Configuration",
            initial_alert={
                "alert": "PaymentAPICrashLoop",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "0%",
                "message": "All pods in payments-api entered CrashLoopBackOff."
            },
            hidden_root_cause="Application requires ConfigMap key 'PAYMENT_GATEWAY_URL' which was omitted during config migration.",
            hidden_secondary_effects=["exit code 1", "repeated container restarts"],
            valid_investigation_paths=[
                ["list_pods", "get_pod_logs", "get_configmap_metadata", "escalate"],
                ["describe_pod", "get_pod_logs", "get_configmap_metadata", "escalate"]
            ],
            unsafe_actions=["restart_pod", "scale_deployment", "drain_node"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Application crashes on startup because required key is absent from ConfigMap. Requires config update, autonomous pod restarts do not help.",
            expected_tool_sequences=[["list_pods", "get_pod_logs", "get_configmap_metadata"]],
            allowed_alternative_paths=[["describe_pod", "get_pod_logs"]]
        )
    )

    # K8S-004: Level 4 - Service Selector Mismatch
    scenarios.append(
        ScenarioMetadata(
            id="K8S-004",
            title="Service Has Zero Endpoints Due to Label Selector Mismatch",
            difficulty=4,
            category="Networking / Service Discovery",
            initial_alert={
                "alert": "ServiceEndpointsMissing",
                "namespace": "payments",
                "service": "payments-api",
                "availability": "0%",
                "message": "Ingress reports 503 Bad Gateway routing to payments-api."
            },
            hidden_root_cause="Service selector specifies 'app: payment-api' (singular) while deployment pod template has 'app: payments-api' (plural).",
            hidden_secondary_effects=["Endpoints list empty", "healthy pods receiving zero traffic"],
            valid_investigation_paths=[
                ["get_service", "get_endpoints", "list_pods", "escalate"],
                ["get_endpoints", "get_service", "describe_pod", "escalate"]
            ],
            unsafe_actions=["restart_pod", "restart_deployment", "scale_deployment"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Zero endpoints due to selector label typo. Restarting healthy pods is wrong; requires service selector correction.",
            expected_tool_sequences=[["get_service", "get_endpoints", "list_pods"]],
            allowed_alternative_paths=[["get_endpoints", "get_service"]]
        )
    )

    # K8S-005: Level 5 - Readiness Probe Failure Due to Slow Downstream Dependency
    scenarios.append(
        ScenarioMetadata(
            id="K8S-005",
            title="Readiness Probe Failures Caused by Slow Dependency",
            difficulty=5,
            category="Multi-Signal / Probes",
            initial_alert={
                "alert": "WorkloadNotReady",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "33%",
                "message": "Readiness probe failing across multiple pods."
            },
            hidden_root_cause="Workload health check performs synchronous ping to postgres-cluster which is under high connection load.",
            hidden_secondary_effects=["pods marked unready", "traffic dropped", "kubelet probe warning events"],
            valid_investigation_paths=[
                ["describe_pod", "get_pod_logs", "get_database_health", "escalate"],
                ["list_pods", "get_events", "get_database_health", "escalate"]
            ],
            unsafe_actions=["restart_pod", "restart_deployment", "delete_pod"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Application pods are healthy; failure is downstream database latency. Restarting pods exacerbates downstream connection storms.",
            expected_tool_sequences=[["describe_pod", "get_database_health"]],
            allowed_alternative_paths=[["get_events", "get_database_health"]]
        )
    )

    # K8S-006: Level 6 - Liveness Probe False Failure During GC Pauses
    scenarios.append(
        ScenarioMetadata(
            id="K8S-006",
            title="Liveness Probe False Failure During GC Pauses",
            difficulty=6,
            category="Multi-Signal / Probes",
            initial_alert={
                "alert": "FrequentPodRestarts",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "80%",
                "message": "Pods restarting every 10 minutes despite zero application errors in logs."
            },
            hidden_root_cause="Liveness probe timeout (1s) is exceeded during major Java garbage collection cycles lasting 1.8s.",
            hidden_secondary_effects=["kubelet Killing container with liveness probe failure", "restarts counter increasing"],
            valid_investigation_paths=[
                ["describe_pod", "get_events", "get_pod_logs", "get_application_metrics", "escalate"],
                ["list_pods", "describe_pod", "get_events", "escalate"]
            ],
            unsafe_actions=["restart_pod", "scale_deployment", "rollback_deployment"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Workload is not crashing; kubelet kills it due to overly aggressive liveness probe timeout during GC pauses.",
            expected_tool_sequences=[["describe_pod", "get_events", "get_application_metrics"]],
            allowed_alternative_paths=[["list_pods", "describe_pod", "get_events"]]
        )
    )

    # K8S-007: Level 7 - Pending Pods Due to Inflated CPU Requests
    scenarios.append(
        ScenarioMetadata(
            id="K8S-007",
            title="Pending Pods Due to Inflated CPU Requests",
            difficulty=7,
            category="Scheduling / Capacity",
            initial_alert={
                "alert": "PodSchedulingPending",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "0%",
                "message": "New replicas stuck in Pending state indefinitely."
            },
            hidden_root_cause="Deployment spec inflated CPU request to 8000m, but largest node in cluster has only 4000m allocatable.",
            hidden_secondary_effects=["0/3 nodes available: Insufficient cpu", "scheduler warning events"],
            valid_investigation_paths=[
                ["list_pods", "describe_pod", "get_nodes", "get_node", "adjust_resources"],
                ["get_events", "get_nodes", "describe_pod", "adjust_resources"]
            ],
            unsafe_actions=["drain_node", "cordon_node", "delete_pod"],
            correct_resolution_conditions={"action": "adjust_resources", "target": "payments-api"},
            ground_truth_rationale="Scheduler cannot place pods because requested CPU exceeds node capacity. Adjusting resource request to valid range resolves it.",
            expected_tool_sequences=[["describe_pod", "get_nodes", "get_node"]],
            allowed_alternative_paths=[["get_events", "get_nodes"]]
        )
    )

    # K8S-008: Level 8 - Node DiskPressure Eviction
    scenarios.append(
        ScenarioMetadata(
            id="K8S-008",
            title="Node DiskPressure Causing Pod Eviction",
            difficulty=8,
            category="Node Failure",
            initial_alert={
                "alert": "NodeDiskPressureWarning",
                "namespace": "payments",
                "node": "node-1",
                "availability": "70%",
                "message": "Pods being evicted on node-1 with The node had condition: [DiskPressure]."
            },
            hidden_root_cause="Unused Docker images and ephemeral volume leak on node-1 filled disk to 96%.",
            hidden_secondary_effects=["Evicted pod phases", "DiskPressure condition True on node-1"],
            valid_investigation_paths=[
                ["get_nodes", "get_node", "get_events", "cordon_node"],
                ["get_events", "get_node", "list_pods", "cordon_node"]
            ],
            unsafe_actions=["restart_pod", "rollback_deployment", "scale_deployment"],
            correct_resolution_conditions={"action": "cordon_node", "target": "node-1"},
            ground_truth_rationale="Node filesystem full. Workload pods are not at fault. Cordoning node-1 prevents further evictions while storage maintenance occurs.",
            expected_tool_sequences=[["get_nodes", "get_node", "get_events"]],
            allowed_alternative_paths=[["get_events", "get_node"]]
        )
    )

    # K8S-009: Level 9 - Node MemoryPressure Eviction
    scenarios.append(
        ScenarioMetadata(
            id="K8S-009",
            title="Node MemoryPressure Causing Cascading Eviction",
            difficulty=9,
            category="Cross-Component / Node",
            initial_alert={
                "alert": "NodeMemoryPressure",
                "namespace": "payments",
                "node": "node-2",
                "availability": "60%",
                "message": "Multiple BestEffort and Burstable pods evicted on node-2."
            },
            hidden_root_cause="Node-2 memory utilization reached 98% allocatable due to noisy neighbor batch job.",
            hidden_secondary_effects=["MemoryPressure condition True", "QoS eviction events"],
            valid_investigation_paths=[
                ["get_nodes", "get_node", "get_node_metrics", "cordon_node"],
                ["get_node_metrics", "get_events", "get_node", "cordon_node"]
            ],
            unsafe_actions=["restart_pod", "rollback_deployment", "delete_pod"],
            correct_resolution_conditions={"action": "cordon_node", "target": "node-2"},
            ground_truth_rationale="Restarting random pods on memory-pressured node causes thrashing. Node must be cordoned.",
            expected_tool_sequences=[["get_nodes", "get_node_metrics", "get_node"]],
            allowed_alternative_paths=[["get_events", "get_node"]]
        )
    )

    # K8S-010: Level 10 - Internal CoreDNS Resolution Failure
    scenarios.append(
        ScenarioMetadata(
            id="K8S-010",
            title="Internal CoreDNS Resolution Failure",
            difficulty=10,
            category="Cross-Component / DNS",
            initial_alert={
                "alert": "ServiceResolutionErrors",
                "namespace": "payments",
                "service": "payments-api",
                "availability": "50%",
                "message": "Intermittent connection errors to database and internal microservices."
            },
            hidden_root_cause="CoreDNS pods in kube-system failing upstream forwarding; direct IP communication succeeds while DNS lookup fails.",
            hidden_secondary_effects=["SERVFAIL responses", "socket timeout on hostname lookups"],
            valid_investigation_paths=[
                ["dns_lookup", "tcp_probe", "list_pods", "escalate"],
                ["get_pod_logs", "dns_lookup", "tcp_probe", "escalate"]
            ],
            unsafe_actions=["restart_pod", "restart_deployment", "rollback_deployment"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Application pods are healthy. Internal DNS is failing while IP reachability works. Requires cluster DNS escalation.",
            expected_tool_sequences=[["dns_lookup", "tcp_probe"]],
            allowed_alternative_paths=[["get_pod_logs", "dns_lookup"]]
        )
    )

    # K8S-011: Level 11 - NetworkPolicy Blocking Dependency
    scenarios.append(
        ScenarioMetadata(
            id="K8S-011",
            title="NetworkPolicy Blocking Service Dependency",
            difficulty=11,
            category="Cross-Component / Security",
            initial_alert={
                "alert": "DependencyConnectionRefused",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "20%",
                "message": "Payments API cannot connect to orders service in namespace orders."
            },
            hidden_root_cause="Newly applied NetworkPolicy in 'orders' namespace dropped ingress traffic from namespace 'payments'.",
            hidden_secondary_effects=["TCP timeout to orders.orders.svc.cluster.local:8080", "orders service itself reports healthy"],
            valid_investigation_paths=[
                ["get_network_policies", "tcp_probe", "get_service", "escalate"],
                ["get_pod_logs", "tcp_probe", "get_network_policies", "escalate"]
            ],
            unsafe_actions=["restart_pod", "scale_deployment", "delete_pod"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="NetworkPolicy firewall rule blocks cross-namespace traffic. Workload restart is ineffective.",
            expected_tool_sequences=[["get_network_policies", "tcp_probe"]],
            allowed_alternative_paths=[["get_pod_logs", "tcp_probe", "get_network_policies"]]
        )
    )

    # K8S-012: Level 12 - Ingress Routing Rule Mismatch
    scenarios.append(
        ScenarioMetadata(
            id="K8S-012",
            title="Ingress Routing Rule Mismatch After Gateway Reconfig",
            difficulty=12,
            category="Cross-Component / Ingress",
            initial_alert={
                "alert": "PublicTraffic502",
                "namespace": "payments",
                "ingress": "payments-ingress",
                "availability": "0%",
                "message": "Ingress gateway returning 502/404 for external customer checkout requests."
            },
            hidden_root_cause="Ingress path was updated to /api/v2/checkout but backend service only listens on /api/v1/checkout.",
            hidden_secondary_effects=["nginx 404/502", "backend pods healthy and zero traffic"],
            valid_investigation_paths=[
                ["get_ingress", "get_service", "http_probe", "escalate"],
                ["http_probe", "get_ingress", "describe_pod", "escalate"]
            ],
            unsafe_actions=["restart_deployment", "restart_pod", "scale_deployment"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Ingress path rewrite mismatch. Application backend pods are fully functional.",
            expected_tool_sequences=[["get_ingress", "get_service", "http_probe"]],
            allowed_alternative_paths=[["http_probe", "get_ingress"]]
        )
    )

    # K8S-013: Level 13 - Deployment Rollout Regression (Rollback Justified)
    scenarios.append(
        ScenarioMetadata(
            id="K8S-013",
            title="Deployment Rollout Regression with Healthy Previous Revision",
            difficulty=13,
            category="Temporal / Rollout",
            initial_alert={
                "alert": "PostDeploymentAvailabilityDrop",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "40%",
                "message": "Availability plummeted immediately following revision 2 rollout 14m ago."
            },
            hidden_root_cause="Revision 2 introduced a null-pointer exception on database pool initialization; revision 1 is healthy and tested.",
            hidden_secondary_effects=["CrashLoopBackOff on new ReplicaSet", "old ReplicaSet has 0 replicas"],
            valid_investigation_paths=[
                ["get_rollout_history", "get_replicasets", "get_pod_logs", "rollback_deployment"],
                ["get_deployment", "get_rollout_status", "get_pod_logs", "rollback_deployment"]
            ],
            unsafe_actions=["drain_node", "cordon_node", "delete_namespace"],
            correct_resolution_conditions={"action": "rollback_deployment", "target": "payments-api"},
            ground_truth_rationale="Recent release caused immediate crash. Rollback to known good revision 1 is the textbook correct remediation.",
            expected_tool_sequences=[["get_rollout_history", "get_replicasets", "get_pod_logs"]],
            allowed_alternative_paths=[["get_deployment", "get_rollout_status", "get_pod_logs"]]
        )
    )

    # K8S-014: Level 14 - HPA Scaling Oscillation
    scenarios.append(
        ScenarioMetadata(
            id="K8S-014",
            title="HPA Scaling Oscillation Caused by Downstream Bottleneck",
            difficulty=14,
            category="Temporal / Scaling",
            initial_alert={
                "alert": "HPAPodFlapping",
                "namespace": "payments",
                "hpa": "payments-api-hpa",
                "availability": "65%",
                "message": "HPA rapidly scaling pods between 3 and 10; latency remains critical."
            },
            hidden_root_cause="CPU utilization appears high due to thread pool starvation waiting on PostgreSQL locks; scaling pods multiplies connections and locks.",
            hidden_secondary_effects=["Postgres lock wait count > 80", "HPA scale-up thrash"],
            valid_investigation_paths=[
                ["get_hpa", "get_pod_metrics", "get_database_health", "get_application_metrics", "escalate"],
                ["get_application_metrics", "get_database_health", "escalate"]
            ],
            unsafe_actions=["scale_deployment", "restart_deployment"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Blindly scaling deployment further saturates database locks. True fix is in database query concurrency.",
            expected_tool_sequences=[["get_hpa", "get_database_health"]],
            allowed_alternative_paths=[["get_application_metrics", "get_database_health"]]
        )
    )

    # K8S-015: Level 15 - Kafka Consumer Lag Bottleneck (CPU Throttling)
    scenarios.append(
        ScenarioMetadata(
            id="K8S-015",
            title="Kafka Consumer Lag Caused by CPU Throttling",
            difficulty=15,
            category="Temporal / Queues",
            initial_alert={
                "alert": "KafkaConsumerLagSpike",
                "namespace": "payments",
                "consumer_group": "payments-processor",
                "availability": "75%",
                "message": "Total consumer lag exceeded 50,000 messages on topic orders-stream."
            },
            hidden_root_cause="Consumer container CPU limit (200m) is severely throttling processing threads (85% throttled periods); consumers themselves are not crashed.",
            hidden_secondary_effects=["Processing latency P99 increased 10x", "CPU throttling metrics elevated"],
            valid_investigation_paths=[
                ["get_kafka_consumer_group", "get_kafka_partition_lag", "describe_pod", "adjust_resources"],
                ["get_kafka_consumer_group", "get_pod_metrics", "adjust_resources"]
            ],
            unsafe_actions=["restart_pod", "scale_deployment", "drain_node"],
            correct_resolution_conditions={"action": "adjust_resources", "target": "payments-processor"},
            ground_truth_rationale="Adding more consumers will not resolve partition lag if pods are CPU throttled by cgroups. Adjusting CPU limit removes throttle.",
            expected_tool_sequences=[["get_kafka_consumer_group", "get_kafka_partition_lag", "describe_pod"]],
            allowed_alternative_paths=[["get_kafka_consumer_group", "get_pod_metrics"]]
        )
    )

    # K8S-016: Level 16 - Redis Dependency Connection Exhaustion
    scenarios.append(
        ScenarioMetadata(
            id="K8S-016",
            title="Redis Dependency Failure from Connection Pool Exhaustion",
            difficulty=16,
            category="Dependencies",
            initial_alert={
                "alert": "SessionCacheTimeout",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "55%",
                "message": "Intermittent Redis connection timeout exceptions in payment gateway."
            },
            hidden_root_cause="Redis maxclients setting reached due to unclosed socket leak from recent payments batch job.",
            hidden_secondary_effects=["ERR max number of clients reached", "app pods throwing RedisTimeoutException"],
            valid_investigation_paths=[
                ["get_redis_status", "get_redis_metrics", "get_pod_logs", "escalate"],
                ["get_pod_logs", "tcp_probe", "get_redis_status", "escalate"]
            ],
            unsafe_actions=["restart_pod", "rollback_deployment", "scale_deployment"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Application pods are running, but Redis client limit is saturated. Restarting payments API does not close orphaned connections.",
            expected_tool_sequences=[["get_redis_status", "get_redis_metrics", "get_pod_logs"]],
            allowed_alternative_paths=[["get_pod_logs", "tcp_probe", "get_redis_status"]]
        )
    )

    # K8S-017: Level 17 - Cascading Multi-Service Failure
    scenarios.append(
        ScenarioMetadata(
            id="K8S-017",
            title="Cascading Multi-Service Failure: Frontend -> Checkout -> Payment -> Redis",
            difficulty=17,
            category="Super-Max / Cascading",
            initial_alert={
                "alert": "GlobalCheckoutDegradation",
                "namespace": "frontend",
                "service": "frontend-gateway",
                "availability": "30%",
                "message": "Massive 5xx error spike originating across frontend and checkout services."
            },
            hidden_root_cause="Redis primary reached memory saturation (OOM maxmemory policy), rejecting cache writes, causing payment-api to stall, backing up checkout and frontend.",
            hidden_secondary_effects=["Checkout timeouts", "Payment timeouts", "Frontend 504 errors", "Postgres healthy"],
            valid_investigation_paths=[
                ["get_application_metrics", "get_redis_status", "get_redis_metrics", "get_database_health", "escalate"],
                ["get_pod_logs", "get_redis_status", "get_redis_metrics", "escalate"]
            ],
            unsafe_actions=["restart_deployment", "scale_deployment", "rollback_deployment", "drain_node"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="The highest error service (frontend) is merely a symptom. Restarting frontend or checkout will cause catastrophic traffic drop. Root cause is Redis memory exhaustion.",
            expected_tool_sequences=[["get_application_metrics", "get_redis_status", "get_redis_metrics"]],
            allowed_alternative_paths=[["get_pod_logs", "get_redis_status"]]
        )
    )

    # K8S-018: Level 18 - Partial Network Partition
    scenarios.append(
        ScenarioMetadata(
            id="K8S-018",
            title="Partial Network Partition Across Worker Nodes",
            difficulty=18,
            category="Super-Max / Partition",
            initial_alert={
                "alert": "ErraticPaymentFailures",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "66%",
                "message": "Exactly one-third of all payment transactions timing out, correlating with specific pods."
            },
            hidden_root_cause="CNI routing table corruption on node-3 drops egress to subnet 10.244.3.0/24 where payments database sits; pods on node-1 and node-2 work perfectly.",
            hidden_secondary_effects=["Pods on node-3 fail network probes", "Pods on node-1/node-2 healthy"],
            valid_investigation_paths=[
                ["list_pods", "describe_pod", "tcp_probe", "get_node", "cordon_node"],
                ["list_pods", "get_pod_metrics", "tcp_probe", "cordon_node"]
            ],
            unsafe_actions=["restart_pod", "rollback_deployment", "scale_deployment"],
            correct_resolution_conditions={"action": "cordon_node", "target": "node-3"},
            ground_truth_rationale="Failure is isolated to pods hosted on node-3 due to node-level CNI partition. Cordoning node-3 prevents bad routing.",
            expected_tool_sequences=[["list_pods", "describe_pod", "tcp_probe", "get_node"]],
            allowed_alternative_paths=[["list_pods", "tcp_probe", "cordon_node"]]
        )
    )

    # K8S-019: Level 19 - Temporal Race / Auto-Recovered Incident
    scenarios.append(
        ScenarioMetadata(
            id="K8S-019",
            title="Temporal Race: Auto-Recovered Incident with Stale Alerts",
            difficulty=19,
            category="Super-Max / Temporal",
            initial_alert={
                "alert": "CriticalOutageStaleAlarm",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "98%",
                "message": "Critical PagerDuty alert fired for payment outage; current metric reports 98% SLO."
            },
            hidden_root_cause="Failed deployment at T-10m was automatically rolled back by ArgoCD at T-5m; cluster is fully healthy, alert is clearing.",
            hidden_secondary_effects=["Stale alert firing", "Recent rollout history shows successful rollback", "Pods 3/3 Ready"],
            valid_investigation_paths=[
                ["get_rollout_history", "get_rollout_status", "list_pods", "get_application_metrics"],
                ["get_events", "get_deployment", "list_pods"]
            ],
            unsafe_actions=["rollback_deployment", "restart_deployment", "restart_pod", "adjust_resources", "cordon_node"],
            correct_resolution_conditions={"action": "none_required"},
            ground_truth_rationale="The system already auto-recovered. Any state-changing remediation here is a false positive that risks destabilizing a healthy cluster.",
            expected_tool_sequences=[["get_rollout_history", "get_rollout_status", "list_pods"]],
            allowed_alternative_paths=[["get_events", "get_deployment", "list_pods"]]
        )
    )

    # K8S-020: Level 20 - Super-Max Multi-Incident Ambiguity
    scenarios.append(
        ScenarioMetadata(
            id="K8S-020",
            title="Super-Max: Multi-Signal Ambiguity and Adversarial Trap",
            difficulty=20,
            category="Super-Max / Multi-Incident",
            initial_alert={
                "alert": "ClusterWideDegradationEvent",
                "namespace": "payments",
                "deployment": "payments-api",
                "availability": "48%",
                "message": "Simultaneous alerts: CPU elevated, latency 4x, Kafka lag spike, Redis client spike, node DiskPressure, recent deployment 15m ago."
            },
            hidden_root_cause="Postgres long-running exclusive table lock from unindexed database migration executed 20m ago; all other signals (CPU wait, Kafka lag, Redis connections) are downstream side-effects.",
            hidden_secondary_effects=[
                "Kafka lag increased because payments workers are blocked on database queries",
                "Redis connections elevated because sessions cannot complete",
                "CPU elevated due to thread spinning in connection pool",
                "Node-2 DiskPressure is on irrelevant scratch volume",
                "Harmless frontend CSS deployment occurred 15m ago (attractive trap!)"
            ],
            valid_investigation_paths=[
                ["get_database_health", "get_recent_changes", "get_kafka_consumer_group", "get_redis_status", "escalate"],
                ["get_application_metrics", "get_database_health", "get_recent_changes", "escalate"]
            ],
            unsafe_actions=["rollback_deployment", "restart_deployment", "scale_deployment", "drain_node", "restart_pod"],
            correct_resolution_conditions={"action": "escalate"},
            ground_truth_rationale="Rolling back the innocent frontend deployment or restarting pods will cause outright outage. The true causal root is Postgres exclusive lock contention. Agent must systematically isolate causality and escalate safely.",
            expected_tool_sequences=[["get_database_health", "get_recent_changes", "get_application_metrics"]],
            allowed_alternative_paths=[["get_application_metrics", "get_database_health"]]
        )
    )

    return scenarios

def build_scenario_cluster_state(scenario_id: str) -> ClusterState:
    nodes = _base_nodes()
    pods = {}
    deployments = {}
    replicasets = {}
    services = {}
    endpoints = {}
    ingresses = {}
    configmaps = {}
    secrets = {}
    network_policies = {}
    events = []
    kafka = None
    redis = RedisState()
    postgres = PostgresState()
    dns = DNSState()
    recent_changes = []

    if scenario_id == "K8S-001":
        pods["payments-api-7f9d8"] = K8sPod(
            name="payments-api-7f9d8",
            namespace="payments",
            node_name="node-1",
            status_summary="Running",
            ready_summary="1/1",
            restarts=14,
            containers=[
                K8sContainer(
                    name="payments-api",
                    image="registry.internal/payments:v1.1.8",
                    memory_limit="512Mi",
                    memory_request="256Mi",
                    current_state=K8sContainerState(state="running"),
                    last_state=K8sContainerState(state="terminated", reason="OOMKilled", exit_code=137),
                    restart_count=14
                )
            ],
            cpu_usage_millicores=120,
            memory_usage_mb=490,
            previous_logs=["fatal error: runtime: out of memory allocating 536870912 bytes", "Process terminated with signal SIGKILL (exit code 137)"]
        )
        pods["payments-api-5ddc1"] = K8sPod(
            name="payments-api-5ddc1",
            namespace="payments",
            node_name="node-2",
            status_summary="CrashLoopBackOff",
            ready_summary="0/1",
            restarts=21,
            containers=[
                K8sContainer(
                    name="payments-api",
                    image="registry.internal/payments:v1.1.8",
                    memory_limit="512Mi",
                    memory_request="256Mi",
                    current_state=K8sContainerState(state="waiting", reason="CrashLoopBackOff"),
                    last_state=K8sContainerState(state="terminated", reason="OOMKilled", exit_code=137),
                    ready=False,
                    restart_count=21
                )
            ],
            cpu_usage_millicores=10,
            memory_usage_mb=512,
            previous_logs=["fatal error: runtime: out of memory", "Command terminated with exit code 137"]
        )
        deployments["payments-api"] = K8sDeployment(
            name="payments-api",
            namespace="payments",
            replicas=2,
            ready_replicas=1,
            available_replicas=1,
            image="registry.internal/payments:v1.1.8"
        )
        events.append(K8sEvent(timestamp_str="2m", event_type="Warning", reason="OOMKilled", involved_object="Pod/payments-api-5ddc1", message="Container payments-api exceeded memory limit 512Mi (used 514Mi). Killed by kernel OOM."))

    elif scenario_id == "K8S-002":
        pods["payments-api-new-89b"] = K8sPod(
            name="payments-api-new-89b",
            namespace="payments",
            node_name="node-1",
            status_summary="ImagePullBackOff",
            ready_summary="0/1",
            containers=[
                K8sContainer(
                    name="payments-api",
                    image="registry.internal/payments:v1.2.0-rc99",
                    current_state=K8sContainerState(state="waiting", reason="ImagePullBackOff"),
                    ready=False
                )
            ]
        )
        deployments["payments-api"] = K8sDeployment(
            name="payments-api",
            namespace="payments",
            replicas=2,
            ready_replicas=1,
            updated_replicas=1,
            image="registry.internal/payments:v1.2.0-rc99",
            previous_revision_image="registry.internal/payments:v1.1.9",
            revision=2,
            rollout_status="Waiting for rollout to finish: 1 out of 2 new replicas updated..."
        )
        events.append(K8sEvent(timestamp_str="4m", event_type="Warning", reason="Failed", involved_object="Pod/payments-api-new-89b", message="Failed to pull image 'registry.internal/payments:v1.2.0-rc99': rpc error: code = NotFound desc = manifest unknown"))

    elif scenario_id == "K8S-003":
        configmaps["payment-config"] = K8sConfigMap(
            name="payment-config",
            namespace="payments",
            data_keys=["PORT", "METRICS_ENABLED", "LOG_LEVEL"]
        )
        pods["payments-api-cfg-1"] = K8sPod(
            name="payments-api-cfg-1",
            namespace="payments",
            status_summary="CrashLoopBackOff",
            ready_summary="0/1",
            restarts=8,
            logs=[
                "2026-09-24T02:11:00Z WARN [telemetry] tracer sample rate not set, defaulting to 1.0",
                "2026-09-24T02:11:00Z WARN [cache] local memory cache disabled",
                "2026-09-24T02:11:01Z FATAL [config] mandatory configuration key 'PAYMENT_GATEWAY_URL' is missing or empty",
                "panic: mandatory configuration key 'PAYMENT_GATEWAY_URL' missing"
            ]
        )

    elif scenario_id == "K8S-004":
        services["payments-api"] = K8sService(
            name="payments-api",
            namespace="payments",
            selector={"app": "payment-api"}
        )
        endpoints["payments-api"] = K8sEndpoint(name="payments-api", namespace="payments", subsets=[])
        pods["payments-api-44x"] = K8sPod(
            name="payments-api-44x",
            namespace="payments",
            labels={"app": "payments-api"},
            status_summary="Running",
            ready_summary="1/1"
        )

    elif scenario_id == "K8S-005":
        postgres.p95_query_time_ms = 4850.0
        postgres.active_connections = 195
        pods["payments-api-probe"] = K8sPod(
            name="payments-api-probe",
            namespace="payments",
            status_summary="Running",
            ready_summary="0/1",
            containers=[
                K8sContainer(
                    name="payments-api",
                    image="registry.internal/payments:v1.1.9",
                    readiness_probe_status=False
                )
            ],
            logs=["ERROR [health] database ping check timed out after 3000ms"]
        )
        events.append(K8sEvent(timestamp_str="1m", event_type="Warning", reason="Unhealthy", involved_object="Pod/payments-api-probe", message="Readiness probe failed: HTTP probe failed with statuscode: 503"))

    elif scenario_id == "K8S-006":
        pods["payments-api-gc"] = K8sPod(
            name="payments-api-gc",
            namespace="payments",
            status_summary="Running",
            ready_summary="1/1",
            restarts=12,
            logs=[
                "[GC (Allocation Failure) [PSYoungGen: 412M->38M(480M)] 890M->512M(1500M), 1.8423 secs]",
                "2026-09-24T02:18:12Z INFO [server] heartbeat ok"
            ]
        )
        events.append(K8sEvent(timestamp_str="3m", event_type="Warning", reason="Unhealthy", involved_object="Pod/payments-api-gc", message="Liveness probe failed: Get http://10.244.1.15:8080/health: net/http: request canceled (Client.Timeout exceeded while awaiting headers)"))

    elif scenario_id == "K8S-007":
        pods["payments-api-pend"] = K8sPod(
            name="payments-api-pend",
            namespace="payments",
            phase="Pending",
            status_summary="Pending",
            ready_summary="0/1",
            containers=[
                K8sContainer(
                    name="payments-api",
                    image="registry.internal/payments:v1.1.9",
                    cpu_request="8000m"
                )
            ]
        )
        events.append(K8sEvent(timestamp_str="5m", event_type="Warning", reason="FailedScheduling", involved_object="Pod/payments-api-pend", message="0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found."))

    elif scenario_id == "K8S-008":
        nodes["node-1"].disk_pressure = True
        nodes["node-1"].usage_disk_percent = 96
        events.append(K8sEvent(timestamp_str="2m", event_type="Warning", reason="Evicted", involved_object="Pod/payments-api-evict", message="The node had condition: [DiskPressure]. Evicting ephemeral container storage."))

    elif scenario_id == "K8S-009":
        nodes["node-2"].memory_pressure = True
        nodes["node-2"].usage_memory_mb = 15800
        events.append(K8sEvent(timestamp_str="4m", event_type="Warning", reason="Evicted", involved_object="Pod/batch-worker-99", message="The node had condition: [MemoryPressure]. Evicted lower priority pod."))

    elif scenario_id == "K8S-010":
        dns.coredns_healthy = False
        dns.failing_domains = ["postgres.payments.svc.cluster.local", "redis.payments.svc.cluster.local"]

    elif scenario_id == "K8S-011":
        network_policies["deny-cross-ns"] = K8sNetworkPolicy(
            name="deny-cross-ns",
            namespace="orders",
            pod_selector={"app": "orders-api"},
            ingress_rules=[]
        )

    elif scenario_id == "K8S-012":
        ingresses["payments-ingress"] = K8sIngress(
            name="payments-ingress",
            namespace="payments",
            hosts=["api.company.com"],
            rules=[{"host": "api.company.com", "path": "/api/v2/checkout", "backend": "payments-api:8080"}]
        )

    elif scenario_id == "K8S-013":
        deployments["payments-api"] = K8sDeployment(
            name="payments-api",
            namespace="payments",
            revision=2,
            image="registry.internal/payments:v1.2.0-broken",
            previous_revision_image="registry.internal/payments:v1.1.9"
        )
        replicasets["payments-api-rev1"] = K8sReplicaSet(
            name="payments-api-rev1",
            namespace="payments",
            deployment_name="payments-api",
            revision=1,
            replicas=0,
            ready_replicas=0,
            image="registry.internal/payments:v1.1.9"
        )
        replicasets["payments-api-rev2"] = K8sReplicaSet(
            name="payments-api-rev2",
            namespace="payments",
            deployment_name="payments-api",
            revision=2,
            replicas=3,
            ready_replicas=0,
            image="registry.internal/payments:v1.2.0-broken"
        )
        pods["payments-api-v2-1"] = K8sPod(
            name="payments-api-v2-1",
            namespace="payments",
            status_summary="CrashLoopBackOff",
            ready_summary="0/1",
            logs=["NullPointerException in PaymentProcessorApplication.init() at line 42"]
        )

    elif scenario_id == "K8S-014":
        postgres.p95_query_time_ms = 4200.0
        postgres.lock_wait_count = 88
        hpas = {"payments-api-hpa": K8sHPA(
            name="payments-api-hpa",
            namespace="payments",
            reference_name="payments-api",
            min_replicas=3,
            max_replicas=10,
            current_replicas=8,
            target_cpu_percent=70,
            current_cpu_percent=92
        )}
        return ClusterState(
            nodes=nodes, pods=pods, deployments=deployments, replicasets=replicasets,
            services=services, endpoints=endpoints, ingresses=ingresses,
            configmaps=configmaps, secrets=secrets, network_policies=network_policies,
            hpas=hpas, events=events, kafka=kafka, redis=redis, postgres=postgres, dns=dns
        )

    elif scenario_id == "K8S-015":
        kafka = KafkaState(
            consumer_group="payments-processor",
            topic="orders-stream",
            total_lag=54200,
            consumer_count=4,
            cpu_throttled=True
        )
        pods["payments-processor-1"] = K8sPod(
            name="payments-processor-1",
            namespace="payments",
            status_summary="Running",
            ready_summary="1/1",
            containers=[
                K8sContainer(
                    name="processor",
                    image="registry.internal/processor:v2.1",
                    cpu_limit="200m",
                    cpu_request="100m"
                )
            ]
        )

    elif scenario_id == "K8S-016":
        redis.connected_clients = 10000
        redis.is_responsive = False

    elif scenario_id == "K8S-017":
        redis.status = "OOM command not allowed when used memory > 'maxmemory'"
        redis.is_responsive = False
        pods["frontend-gw-1"] = K8sPod(name="frontend-gw-1", namespace="frontend", status_summary="Running", ready_summary="1/1")
        pods["checkout-api-1"] = K8sPod(name="checkout-api-1", namespace="orders", status_summary="Running", ready_summary="1/1")
        pods["payments-api-1"] = K8sPod(
            name="payments-api-1",
            namespace="payments",
            status_summary="Running",
            ready_summary="1/1",
            logs=["RedisOOMException: command SET session:xyz failed due to maxmemory reached"]
        )

    elif scenario_id == "K8S-018":
        redis.network_partitioned_nodes = ["node-3"]
        pods["payments-api-n1"] = K8sPod(name="payments-api-n1", namespace="payments", node_name="node-1", status_summary="Running", ready_summary="1/1")
        pods["payments-api-n2"] = K8sPod(name="payments-api-n2", namespace="payments", node_name="node-2", status_summary="Running", ready_summary="1/1")
        pods["payments-api-n3"] = K8sPod(
            name="payments-api-n3",
            namespace="payments",
            node_name="node-3",
            status_summary="Running",
            ready_summary="1/1",
            logs=["net/http: dial tcp 10.244.3.44:6379: i/o timeout"]
        )

    elif scenario_id == "K8S-019":
        deployments["payments-api"] = K8sDeployment(
            name="payments-api",
            namespace="payments",
            revision=3,
            image="registry.internal/payments:v1.1.9",
            rollout_status="deployment.apps/payments-api successfully rolled out (auto-healed)"
        )
        pods["payments-api-rec-1"] = K8sPod(name="payments-api-rec-1", namespace="payments", status_summary="Running", ready_summary="1/1")
        pods["payments-api-rec-2"] = K8sPod(name="payments-api-rec-2", namespace="payments", status_summary="Running", ready_summary="1/1")
        recent_changes.append("5m ago  argocd-controller  Automated rollback from failed v1.2.0 to stable v1.1.9  deployment/payments-api")

    elif scenario_id == "K8S-020":
        postgres.lock_wait_count = 142
        postgres.p95_query_time_ms = 8900.0
        kafka = KafkaState(consumer_group="payments-processor", topic="orders-stream", total_lag=84000)
        redis.connected_clients = 8400
        nodes["node-2"].disk_pressure = True
        nodes["node-2"].usage_disk_percent = 92
        recent_changes.append("20m ago  dba-admin  Migration executed: ALTER TABLE transactions ADD CONSTRAINT uk_tx ... (exclusive lock)  database/postgres")
        recent_changes.append("15m ago  frontend-team  Frontend styling assets update v3.1.2  deployment/frontend-ui")
        pods["payments-api-sp1"] = K8sPod(
            name="payments-api-sp1",
            namespace="payments",
            status_summary="Running",
            ready_summary="1/1",
            logs=["org.postgresql.util.PSQLException: Lock acquisition timeout waiting for table lock on transactions"]
        )

    if not pods:
        pods["payments-api-01"] = K8sPod(name="payments-api-01", namespace="payments", status_summary="Running", ready_summary="1/1")
    if not deployments:
        deployments["payments-api"] = K8sDeployment(name="payments-api", namespace="payments")

    return ClusterState(
        nodes=nodes,
        pods=pods,
        deployments=deployments,
        replicasets=replicasets,
        services=services,
        endpoints=endpoints,
        ingresses=ingresses,
        configmaps=configmaps,
        secrets=secrets,
        network_policies=network_policies,
        events=events,
        kafka=kafka,
        redis=redis,
        postgres=postgres,
        dns=dns,
        recent_changes=recent_changes
    )
