"""
Kubernetes Tool Catalog and Formatter Engine.
Generates realistic, production-grade kubectl and cloud infrastructure outputs.
Provides deterministic evidence hashing and schemas for LLM tool calling.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from backend.models.k8s_resources import ClusterState, K8sPod, K8sEvent
from backend.models.schema import ActionRisk, InformationGain
from backend.simulator.cluster import KubernetesSimulator

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_cluster_state",
            "description": "Get high-level summary of the cluster health, nodes, and active workloads.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nodes",
            "description": "List all Kubernetes nodes in the cluster with status, roles, age, and version.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_node",
            "description": "Inspect detailed specifications, conditions, and capacity of a specific node.",
            "parameters": {
                "type": "object",
                "properties": {"node_name": {"type": "string", "description": "Target node name"}},
                "required": ["node_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_node_metrics",
            "description": "Get current CPU, memory, and disk usage metrics for cluster nodes.",
            "parameters": {
                "type": "object",
                "properties": {"node_name": {"type": "string", "description": "Optional node filter"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_pods",
            "description": "List pods in a specific namespace or across all namespaces with status, ready count, restarts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Namespace to filter, or empty for all"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod",
            "description": "Get specifications and status for a single pod.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Name of the pod"},
                    "namespace": {"type": "string", "description": "Pod namespace"},
                },
                "required": ["pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_pod",
            "description": "Show detailed description of a pod including containers, conditions, volume mounts, and recent events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Name of the pod"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_metrics",
            "description": "Get CPU and memory consumption metrics for pods.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Optional pod name"},
                    "namespace": {"type": "string", "description": "Optional namespace"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "Retrieve stdout/stderr logs from a pod container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Name of the pod"},
                    "namespace": {"type": "string", "description": "Namespace"},
                    "tail_lines": {"type": "integer", "description": "Number of lines to read"},
                },
                "required": ["pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_previous_pod_logs",
            "description": "Retrieve logs from the previously terminated container instance in a pod.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Name of the pod"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "List recent Kubernetes events across the cluster.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_namespace_events",
            "description": "List events in a specific namespace.",
            "parameters": {
                "type": "object",
                "properties": {"namespace": {"type": "string", "description": "Namespace"}},
                "required": ["namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cluster_events",
            "description": "Retrieve cluster-wide warning and error events.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_deployment",
            "description": "Get deployment specification, replica status, and selectors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string", "description": "Name of deployment"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["deployment_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_replicasets",
            "description": "List ReplicaSets associated with deployments.",
            "parameters": {
                "type": "object",
                "properties": {"namespace": {"type": "string", "description": "Namespace"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rollout_status",
            "description": "Check current rollout status of a deployment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string", "description": "Deployment name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["deployment_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rollout_history",
            "description": "View deployment revision history and applied changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string", "description": "Deployment name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["deployment_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_service",
            "description": "Inspect Kubernetes Service definition and selector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Service name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["service_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_endpoints",
            "description": "Inspect Service Endpoints addresses and target pods.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Service name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["service_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_endpointslices",
            "description": "Inspect EndpointSlice resources for scalable routing.",
            "parameters": {
                "type": "object",
                "properties": {"namespace": {"type": "string", "description": "Namespace"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ingress",
            "description": "Get Ingress resource routing rules and TLS settings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingress_name": {"type": "string", "description": "Ingress name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_network_policies",
            "description": "List NetworkPolicy objects governing pod traffic.",
            "parameters": {
                "type": "object",
                "properties": {"namespace": {"type": "string", "description": "Namespace"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hpa",
            "description": "Inspect HorizontalPodAutoscaler configuration and target utilization.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hpa_name": {"type": "string", "description": "HPA name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pdb",
            "description": "Inspect PodDisruptionBudget requirements and allowed disruptions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pdb_name": {"type": "string", "description": "PDB name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_resource_quota",
            "description": "Get namespace compute and storage resource quotas.",
            "parameters": {
                "type": "object",
                "properties": {"namespace": {"type": "string", "description": "Namespace"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_limit_range",
            "description": "Inspect default/min/max resource limits enforced in namespace.",
            "parameters": {
                "type": "object",
                "properties": {"namespace": {"type": "string", "description": "Namespace"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_configmap_metadata",
            "description": "Inspect keys and metadata of ConfigMaps without exposing secrets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "configmap_name": {"type": "string", "description": "ConfigMap name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["configmap_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_secret_metadata",
            "description": "Inspect metadata and key names of Secrets (values redacted).",
            "parameters": {
                "type": "object",
                "properties": {
                    "secret_name": {"type": "string", "description": "Secret name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["secret_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dns_lookup",
            "description": "Perform synthetic DNS query from within the cluster.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain name to resolve"}
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "http_probe",
            "description": "Execute synthetic HTTP probe against an endpoint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "HTTP URL to probe"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tcp_probe",
            "description": "Check TCP socket reachability on target host and port.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Host IP or hostname"},
                    "port": {"type": "integer", "description": "TCP port"}
                },
                "required": ["host", "port"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_kubelet_status",
            "description": "Inspect node kubelet daemon health and log status.",
            "parameters": {
                "type": "object",
                "properties": {"node_name": {"type": "string", "description": "Node name"}},
                "required": ["node_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_application_metrics",
            "description": "Fetch Prometheus golden signals for a workload.",
            "parameters": {
                "type": "object",
                "properties": {"service": {"type": "string", "description": "Service name"}},
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_kafka_consumer_group",
            "description": "Get Kafka consumer group status and partition assignment.",
            "parameters": {
                "type": "object",
                "properties": {"group_name": {"type": "string", "description": "Consumer group"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_kafka_partition_lag",
            "description": "Inspect lag across Kafka topic partitions.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "description": "Topic name"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_redis_status",
            "description": "Check Redis instance health, connectivity, and info.",
            "parameters": {
                "type": "object",
                "properties": {"service_name": {"type": "string", "description": "Redis service name"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_redis_metrics",
            "description": "Inspect Redis memory, connected clients, and latency stats.",
            "parameters": {
                "type": "object",
                "properties": {"service_name": {"type": "string", "description": "Redis service name"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_health",
            "description": "Inspect PostgreSQL health, active connections, and query metrics.",
            "parameters": {
                "type": "object",
                "properties": {"db_name": {"type": "string", "description": "Database cluster name"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_changes",
            "description": "Inspect audit log of recent deployments, rollouts, or config changes in cluster.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restart_pod",
            "description": "Restart a specific pod by issuing an API delete to let controller recreate it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Pod name to restart"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scale_deployment",
            "description": "Scale replica count of a deployment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string", "description": "Deployment name"},
                    "replicas": {"type": "integer", "description": "Target replica count"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["deployment_name", "replicas"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rollback_deployment",
            "description": "Roll back a deployment to its previous stable revision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string", "description": "Deployment name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["deployment_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_resources",
            "description": "Adjust CPU and memory resource requests or limits for a workload container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target deployment or pod"},
                    "memory_limit": {"type": "string", "description": "New memory limit (e.g. 1024Mi)"},
                    "cpu_limit": {"type": "string", "description": "New CPU limit (e.g. 1000m)"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cordon_node",
            "description": "Mark a node as unschedulable to prevent new pods from landing on it.",
            "parameters": {
                "type": "object",
                "properties": {"node_name": {"type": "string", "description": "Node name"}},
                "required": ["node_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drain_node",
            "description": "Drain all non-daemonset pods from a node for maintenance.",
            "parameters": {
                "type": "object",
                "properties": {"node_name": {"type": "string", "description": "Node name"}},
                "required": ["node_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_pod",
            "description": "Directly delete a pod from the cluster.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Pod name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restart_deployment",
            "description": "Trigger a rolling restart of all pods in a deployment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string", "description": "Deployment name"},
                    "namespace": {"type": "string", "description": "Namespace"},
                },
                "required": ["deployment_name"],
            },
        },
    },
]

class ToolExecutionEngine:
    @staticmethod
    def execute(
        simulator: KubernetesSimulator, tool_name: str, args: Dict[str, Any]
    ) -> Tuple[str, bool, ActionRisk, InformationGain]:
        state = simulator.state
        ns = args.get("namespace", "payments")

        action_names = {
            "restart_pod",
            "scale_deployment",
            "rollback_deployment",
            "adjust_resources",
            "cordon_node",
            "drain_node",
            "delete_pod",
            "restart_deployment",
        }
        if tool_name in action_names:
            success, msg, risk = simulator.execute_action(tool_name, args)
            return msg, True, risk, InformationGain.HIGH

        risk = ActionRisk.READ_ONLY
        info_gain = InformationGain.MEDIUM

        if tool_name == "get_cluster_state":
            nodes_ready = sum(1 for n in state.nodes.values() if n.status == "Ready")
            pods_running = sum(1 for p in state.pods.values() if p.status_summary == "Running")
            output = (
                f"Cluster: {state.name}
"
                f"Nodes: {nodes_ready}/{len(state.nodes)} Ready
"
                f"Pods: {pods_running}/{len(state.pods)} Running
"
                f"Namespaces: {', '.join(state.namespaces)}
"
            )
            return output, False, risk, InformationGain.LOW

        elif tool_name == "get_nodes":
            lines = ["NAME      STATUS   ROLES    AGE   VERSION"]
            for n in state.nodes.values():
                status = "Ready" if not n.unschedulable else "Ready,SchedulingDisabled"
                if not n.ready_condition:
                    status = "NotReady"
                lines.append(f"{n.name:<9} {status:<8} <none>   42d   v1.30.2")
            return "
".join(lines), False, risk, InformationGain.MEDIUM

        elif tool_name == "get_node":
            node_name = args.get("node_name", "node-1")
            node = state.nodes.get(node_name)
            if not node:
                return f"Error from server (NotFound): nodes '{node_name}' not found", False, risk, InformationGain.LOW
            cond_lines = [
                f"  Ready:            {node.ready_condition}",
                f"  MemoryPressure:   {node.memory_pressure}",
                f"  DiskPressure:     {node.disk_pressure}",
                f"  PIDPressure:      {node.pid_pressure}",
            ]
            output = (
                f"Name:               {node.name}
"
                f"Status:             {node.status}
"
                f"Unschedulable:      {node.unschedulable}
"
                f"Conditions:
" + "
".join(cond_lines) + "
"
                f"Capacity:
"
                f"  cpu:              {node.capacity_cpu}
"
                f"  memory:           {node.capacity_memory}
"
                f"  ephemeral-storage:{node.capacity_storage}
"
                f"Allocatable:
"
                f"  cpu:              {node.allocatable_cpu}
"
                f"  memory:           {node.allocatable_memory}
"
            )
            return output, False, risk, InformationGain.HIGH if (node.memory_pressure or node.disk_pressure) else InformationGain.MEDIUM

        elif tool_name == "get_node_metrics":
            lines = ["NAME      CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%"]
            for n in state.nodes.values():
                cpu_cores = f"{n.usage_cpu_millicores}m"
                mem_mb = f"{n.usage_memory_mb}Mi"
                lines.append(f"{n.name:<9} {cpu_cores:<12} 31%    {mem_mb:<15} {int(n.usage_memory_mb/16000*100)}%")
            return "
".join(lines), False, risk, InformationGain.MEDIUM

        elif tool_name == "list_pods":
            lines = ["NAME                                READY   STATUS             RESTARTS   AGE"]
            for p in state.pods.values():
                if ns and ns != "all" and p.namespace != ns:
                    continue
                lines.append(f"{p.name:<35} {p.ready_summary:<7} {p.status_summary:<18} {p.restarts:<10} {p.age}")
            return "
".join(lines), False, risk, InformationGain.HIGH

        elif tool_name == "get_pod":
            pod_name = args.get("pod_name", "")
            pod = state.pods.get(pod_name)
            if not pod:
                for p in state.pods.values():
                    if pod_name in p.name:
                        pod = p
                        break
            if not pod:
                return f"Error from server (NotFound): pods '{pod_name}' not found", False, risk, InformationGain.LOW
            output = (
                f"Name:         {pod.name}
"
                f"Namespace:    {pod.namespace}
"
                f"Node:         {pod.node_name}
"
                f"Status:       {pod.status_summary}
"
                f"IP:           {pod.ip}
"
                f"QoS Class:    {pod.qos_class}
"
                f"Restarts:     {pod.restarts}
"
            )
            return output, False, risk, InformationGain.MEDIUM

        elif tool_name == "describe_pod":
            pod_name = args.get("pod_name", "")
            pod = state.pods.get(pod_name)
            if not pod:
                for p in state.pods.values():
                    if pod_name in p.name:
                        pod = p
                        break
            if not pod:
                return f"Error from server (NotFound): pods '{pod_name}' not found", False, risk, InformationGain.LOW

            c_info = []
            for c in pod.containers:
                last_state_str = "    None"
                if c.last_state:
                    last_state_str = (
                        f"    Terminated:
"
                        f"      Reason:       {c.last_state.reason}
"
                        f"      Exit Code:    {c.last_state.exit_code}
"
                        f"      Finished:     12m ago"
                    )
                c_info.append(
                    f"  {c.name}:
"
                    f"    Image:          {c.image}
"
                    f"    State:          {c.current_state.state} ({c.current_state.reason or 'Normal'})
"
                    f"    Last State:
{last_state_str}
"
                    f"    Ready:          {c.ready}
"
                    f"    Restart Count:  {c.restart_count}
"
                    f"    Limits:
"
                    f"      cpu:          {c.cpu_limit}
"
                    f"      memory:       {c.memory_limit}
"
                    f"    Requests:
"
                    f"      cpu:          {c.cpu_request}
"
                    f"      memory:       {c.memory_request}"
                )

            ev_lines = []
            for ev in state.events:
                if pod.name in ev.involved_object:
                    ev_lines.append(f"  {ev.event_type:<7}  {ev.reason:<14}  {ev.message}")

            output = (
                f"Name:             {pod.name}
"
                f"Namespace:        {pod.namespace}
"
                f"Node:             {pod.node_name}
"
                f"Status:           {pod.status_summary}
"
                f"QoS Class:        {pod.qos_class}
"
                f"Containers:
" + "
".join(c_info) + "
"
                f"Events:
" + ("
".join(ev_lines) if ev_lines else "  <none>")
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_pod_metrics":
            lines = ["NAME                                CPU(millicores)   MEMORY(bytes)"]
            for p in state.pods.values():
                if ns and ns != "all" and p.namespace != ns:
                    continue
                lines.append(f"{p.name:<35} {p.cpu_usage_millicores}m               {p.memory_usage_mb}Mi")
            return "
".join(lines), False, risk, InformationGain.HIGH

        elif tool_name == "get_pod_logs":
            pod_name = args.get("pod_name", "")
            pod = state.pods.get(pod_name)
            if not pod:
                for p in state.pods.values():
                    if pod_name in p.name:
                        pod = p
                        break
            if not pod:
                return f"Error from server (NotFound): pods '{pod_name}' not found", False, risk, InformationGain.LOW
            if pod.logs:
                return "
".join(pod.logs), False, risk, InformationGain.HIGH
            return "2026-09-24T02:00:10.124Z INFO [server] service starting on :8080
2026-09-24T02:00:10.890Z INFO [health] readiness probe initialized", False, risk, InformationGain.MEDIUM

        elif tool_name == "get_previous_pod_logs":
            pod_name = args.get("pod_name", "")
            pod = state.pods.get(pod_name)
            if not pod:
                for p in state.pods.values():
                    if pod_name in p.name:
                        pod = p
                        break
            if not pod:
                return f"Error from server (NotFound): pods '{pod_name}' not found", False, risk, InformationGain.LOW
            if pod.previous_logs:
                return "
".join(pod.previous_logs), False, risk, InformationGain.HIGH
            return "fatal error: runtime: out of memory allocating 536870912 bytes
Process terminated with signal SIGKILL (exit code 137)", False, risk, InformationGain.HIGH

        elif tool_name in ["get_events", "get_namespace_events", "get_cluster_events"]:
            lines = ["LAST SEEN   TYPE      REASON              OBJECT                         MESSAGE"]
            for ev in state.events:
                if tool_name == "get_namespace_events" and ns and ns not in ev.involved_object:
                    continue
                lines.append(f"{ev.timestamp_str:<11} {ev.event_type:<9} {ev.reason:<19} {ev.involved_object:<30} {ev.message}")
            return "
".join(lines) if len(lines) > 1 else "No events found.", False, risk, InformationGain.HIGH

        elif tool_name == "get_deployment":
            dep_name = args.get("deployment_name", "")
            dep = state.deployments.get(dep_name)
            if not dep:
                for d in state.deployments.values():
                    if dep_name in d.name:
                        dep = d
                        break
            if not dep:
                return f"Error from server (NotFound): deployments.apps '{dep_name}' not found", False, risk, InformationGain.LOW
            output = (
                f"Name:                   {dep.name}
"
                f"Namespace:              {dep.namespace}
"
                f"Replicas:               {dep.replicas} desired | {dep.updated_replicas} updated | {dep.ready_replicas} total | {dep.available_replicas} available
"
                f"Selector:               {json.dumps(dep.selector_labels)}
"
                f"Image:                  {dep.image}
"
                f"Current Revision:       {dep.revision}
"
                f"Rollout Status:         {dep.rollout_status}
"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_replicasets":
            lines = ["NAME                         DESIRED   CURRENT   READY   AGE   IMAGE"]
            for rs in state.replicasets.values():
                lines.append(f"{rs.name:<28} {rs.replicas:<9} {rs.replicas:<9} {rs.ready_replicas:<7} 18m   {rs.image}")
            return "
".join(lines), False, risk, InformationGain.HIGH

        elif tool_name == "get_rollout_status":
            dep_name = args.get("deployment_name", "")
            dep = state.deployments.get(dep_name)
            if dep:
                return dep.rollout_status, False, risk, InformationGain.HIGH
            return "Waiting for deployment rollout to finish: 1 out of 3 new replicas have been updated...", False, risk, InformationGain.HIGH

        elif tool_name == "get_rollout_history":
            dep_name = args.get("deployment_name", "")
            dep = state.deployments.get(dep_name)
            rev = dep.revision if dep else 2
            prev_img = dep.previous_revision_image if dep else "v1.1.9"
            curr_img = dep.image if dep else "v1.2.0"
            output = (
                f"deployment.apps/{dep_name}
"
                f"REVISION  CHANGE-CAUSE
"
                f"1         Image update to {prev_img} (stable baseline)
"
                f"2         Image update to {curr_img} (deployed 14 minutes ago)
"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_service":
            svc_name = args.get("service_name", "")
            svc = state.services.get(svc_name)
            if not svc:
                for s in state.services.values():
                    if svc_name in s.name:
                        svc = s
                        break
            if not svc:
                return f"Error from server (NotFound): services '{svc_name}' not found", False, risk, InformationGain.LOW
            output = (
                f"Name:              {svc.name}
"
                f"Namespace:         {svc.namespace}
"
                f"Type:              {svc.service_type}
"
                f"IP:                {svc.cluster_ip}
"
                f"Port:              http 80/TCP
"
                f"TargetPort:        8080/TCP
"
                f"Selector:          {json.dumps(svc.selector)}
"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_endpoints":
            svc_name = args.get("service_name", "")
            ep = state.endpoints.get(svc_name)
            if not ep:
                for e in state.endpoints.values():
                    if svc_name in e.name:
                        ep = e
                        break
            if not ep:
                return f"Error from server (NotFound): endpoints '{svc_name}' not found", False, risk, InformationGain.LOW
            if not ep.subsets:
                return f"NAME                  ENDPOINTS
{svc_name:<21} <none>", False, risk, InformationGain.HIGH
            addrs = [f"{a['ip']}:{a.get('port', 8080)}" for sub in ep.subsets for a in sub.get("addresses", [])]
            return f"NAME                  ENDPOINTS
{svc_name:<21} {', '.join(addrs)}", False, risk, InformationGain.HIGH

        elif tool_name == "get_endpointslices":
            return "NAME                       ADDRESSTYPE   PORTS   ENDPOINTS                  AGE
payments-api-slice-9f12    IPv4          8080    10.244.1.15,10.244.2.19    12m", False, risk, InformationGain.MEDIUM

        elif tool_name == "get_ingress":
            lines = ["NAME             CLASS    HOSTS                   ADDRESS        PORTS     AGE"]
            for ing in state.ingresses.values():
                hosts = ",".join(ing.hosts)
                lines.append(f"{ing.name:<16} nginx    {hosts:<23} 198.51.100.2   80, 443   14d")
            return "
".join(lines), False, risk, InformationGain.MEDIUM

        elif tool_name == "get_network_policies":
            if not state.network_policies:
                return "No network policies found in namespace.", False, risk, InformationGain.MEDIUM
            lines = ["NAME                       POD-SELECTOR           AGE"]
            for np in state.network_policies.values():
                sel = json.dumps(np.pod_selector)
                lines.append(f"{np.name:<26} {sel:<22} 5d")
            return "
".join(lines), False, risk, InformationGain.HIGH

        elif tool_name == "get_hpa":
            lines = ["NAME             REFERENCE                   TARGETS         MINPODS   MAXPODS   REPLICAS   AGE"]
            for h in state.hpas.values():
                lines.append(f"{h.name:<16} Deployment/{h.reference_name:<16} {h.current_cpu_percent}%/{h.target_cpu_percent}%   {h.min_replicas:<9} {h.max_replicas:<9} {h.current_replicas:<10} 2d")
            return "
".join(lines), False, risk, InformationGain.HIGH

        elif tool_name == "get_pdb":
            lines = ["NAME             MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE"]
            for p in state.pdbs.values():
                min_a = p.min_available if p.min_available is not None else "N/A"
                max_u = p.max_unavailable if p.max_unavailable is not None else "N/A"
                lines.append(f"{p.name:<16} {min_a:<15} {max_u:<17} {p.disruptions_allowed:<21} 5d")
            return "
".join(lines), False, risk, InformationGain.MEDIUM

        elif tool_name == "get_resource_quota":
            lines = ["NAME             RESOURCE         REQUESTED   LIMIT"]
            for rq in state.resource_quotas.values():
                for k, v in rq.hard.items():
                    used = rq.used.get(k, "0")
                    lines.append(f"{rq.name:<16} {k:<16} {used:<11} {v}")
            return "
".join(lines) if len(lines) > 1 else "No resource quotas found in namespace.", False, risk, InformationGain.HIGH

        elif tool_name == "get_limit_range":
            lines = ["NAME             RESOURCE   DEFAULT_REQ   DEFAULT_LIM   MIN   MAX"]
            for lr in state.limit_ranges.values():
                lines.append(f"{lr.name:<16} memory     256Mi         512Mi         64Mi  4Gi")
            return "
".join(lines) if len(lines) > 1 else "No limit ranges found in namespace.", False, risk, InformationGain.MEDIUM

        elif tool_name == "get_configmap_metadata":
            cm_name = args.get("configmap_name", "")
            cm = state.configmaps.get(cm_name)
            if not cm:
                for c in state.configmaps.values():
                    if cm_name in c.name:
                        cm = c
                        break
            if not cm:
                return f"Error from server (NotFound): configmaps '{cm_name}' not found", False, risk, InformationGain.LOW
            output = (
                f"Name:         {cm.name}
"
                f"Namespace:    {cm.namespace}
"
                f"Data Keys:
  - " + "
  - ".join(cm.data_keys)
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_secret_metadata":
            sec_name = args.get("secret_name", "")
            sec = state.secrets.get(sec_name)
            if not sec:
                return f"Error from server (NotFound): secrets '{sec_name}' not found", False, risk, InformationGain.LOW
            output = (
                f"Name:         {sec.name}
"
                f"Namespace:    {sec.namespace}
"
                f"Type:         {sec.type_name}
"
                f"Data Keys (values redacted): {', '.join(sec.data_keys)}"
            )
            return output, False, risk, InformationGain.MEDIUM

        elif tool_name == "dns_lookup":
            domain = args.get("domain", "")
            if state.dns and not state.dns.coredns_healthy:
                return f"Server: 10.96.0.10
Address: 10.96.0.10#53
** server can't find {domain}: SERVFAIL", False, risk, InformationGain.HIGH
            if state.dns and domain in state.dns.failing_domains:
                return f"Server: 10.96.0.10
Address: 10.96.0.10#53
** server can't find {domain}: NXDOMAIN", False, risk, InformationGain.HIGH
            return f"Server: 10.96.0.10
Address: 10.96.0.10#53
Name: {domain}
Address: 10.96.44.18", False, risk, InformationGain.HIGH

        elif tool_name == "http_probe":
            url = args.get("url", "")
            if "fail" in url or "unhealthy" in url or any(p.status_summary != "Running" for p in state.pods.values()):
                return "HTTP/1.1 503 Service Unavailable
Content-Type: text/plain
Connection: close

upstream connect error or disconnect/reset before headers", False, risk, InformationGain.HIGH
            return "HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 28

{"status":"ok","uptime":18420}", False, risk, InformationGain.MEDIUM

        elif tool_name == "tcp_probe":
            host = args.get("host", "")
            port = args.get("port", 80)
            if state.redis and "redis" in host and not state.redis.is_responsive:
                return f"Connection to {host}:{port} failed: connection refused", False, risk, InformationGain.HIGH
            return f"Connected to {host}:{port} successfully in 1.4ms (TCP SYN/ACK ok).", False, risk, InformationGain.MEDIUM

        elif tool_name == "get_kubelet_status":
            node_name = args.get("node_name", "node-1")
            node = state.nodes.get(node_name)
            status = node.kubelet_status if node else "Active (running)"
            return f"● kubelet.service - kubelet: The Kubernetes Node Agent
   Loaded: loaded (/lib/systemd/system/kubelet.service)
   Active: {status}
   Main PID: 1204 (kubelet)", False, risk, InformationGain.MEDIUM

        elif tool_name == "get_application_metrics":
            svc = args.get("service", "payments-api")
            output = (
                f"Target Service: {svc}
"
                f"Request Rate: 428 req/sec
"
                f"Error Rate (5xx): 8.4%
"
                f"Latency P50: 24ms
"
                f"Latency P95: 1840ms
"
                f"Latency P99: 4120ms
"
                f"Downstream Dependency Wait: 88% of request duration spent waiting for backend socket"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_kafka_consumer_group":
            if not state.kafka:
                return "Kafka cluster not active in this cluster.", False, risk, InformationGain.LOW
            k = state.kafka
            throttled_msg = " [WARNING: CPU Throttling detected on consumer container]" if k.cpu_throttled else ""
            output = (
                f"GROUP:            {k.consumer_group}
"
                f"TOPIC:            {k.topic}
"
                f"PARTITIONS:       {k.partition_count}
"
                f"TOTAL-LAG:        {k.total_lag}
"
                f"ACTIVE-CONSUMERS: {k.consumer_count}
"
                f"STATUS:           Stable{throttled_msg}"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_kafka_partition_lag":
            if not state.kafka:
                return "No Kafka partition lag data available.", False, risk, InformationGain.LOW
            lines = ["PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG   CONSUMER-ID"]
            for i in range(state.kafka.partition_count):
                lag = state.kafka.total_lag // state.kafka.partition_count
                lines.append(f"{i:<10} {10000+i*500:<15} {10000+i*500+lag:<15} {lag:<5} consumer-instance-{i%2}")
            return "
".join(lines), False, risk, InformationGain.HIGH

        elif tool_name == "get_redis_status":
            if not state.redis:
                return "No Redis service configured in namespace.", False, risk, InformationGain.LOW
            r = state.redis
            output = (
                f"# Server
redis_version: 7.2.4
redis_mode: standalone
"
                f"role: master
connected_clients: {r.connected_clients}
"
                f"used_memory_human: {r.used_memory_human}
"
                f"maxmemory_human: {r.max_memory_human}
"
                f"ping_status: {r.status}
"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_redis_metrics":
            if not state.redis:
                return "No Redis metrics available.", False, risk, InformationGain.LOW
            r = state.redis
            output = (
                f"instantaneous_ops_per_sec: 1420
"
                f"hit_rate: 94.2%
"
                f"connected_clients: {r.connected_clients}
"
                f"blocked_clients: 0
"
                f"used_memory_rss_human: {r.used_memory_human}
"
            )
            return output, False, risk, InformationGain.MEDIUM

        elif tool_name == "get_database_health":
            if not state.postgres:
                return "No Postgres database configured.", False, risk, InformationGain.LOW
            p = state.postgres
            output = (
                f"Database Server: {p.service_name}
"
                f"Status: {p.status}
"
                f"Active Connections: {p.active_connections} / {p.max_connections}
"
                f"P95 Query Execution Time: {p.p95_query_time_ms}ms
"
                f"Lock Wait Count: {p.lock_wait_count}
"
            )
            return output, False, risk, InformationGain.HIGH

        elif tool_name == "get_recent_changes":
            if state.recent_changes:
                lines = ["TIMESTAMP               USER               ACTION                         RESOURCE"]
                for chg in state.recent_changes:
                    lines.append(f"{chg}")
                return "
".join(lines), False, risk, InformationGain.HIGH
            return (
                "TIMESTAMP               USER               ACTION                         RESOURCE
"
                "15m ago                 cicd-runner        Deployment rollout update      deployment/payments-api
"
                "45m ago                 platform-admin     ConfigMap sync                 configmap/payment-config",
                False,
                risk,
                InformationGain.HIGH,
            )

        return f"Tool {tool_name} not implemented.", False, risk, InformationGain.LOW
