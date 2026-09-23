"""
Deterministic Kubernetes Cluster Simulator.
Maintains visible cluster state and hidden ground truth, supporting realistic
state mutations without mutating real infrastructure.
"""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from backend.models.k8s_resources import (
    ClusterState,
    K8sPod,
    K8sContainer,
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
from backend.models.schema import ActionRisk


class KubernetesSimulator:
    """
    High-fidelity deterministic simulator of a Kubernetes cluster environment.
    Exposes visible state via diagnostic queries and handles state-changing mutations.
    """

    def __init__(
        self,
        cluster_state: ClusterState,
        scenario_id: str,
        hidden_root_cause: str,
        unsafe_actions: List[str],
        resolution_conditions: Dict[str, Any],
    ) -> None:
        self.state: ClusterState = copy.deepcopy(cluster_state)
        self.scenario_id: str = scenario_id
        self.hidden_root_cause: str = hidden_root_cause
        self.unsafe_actions: List[str] = unsafe_actions
        self.resolution_conditions: Dict[str, Any] = resolution_conditions
        self.resolved: bool = False
        self.unsafe_action_occurred: bool = False
        self.prohibited_actions_taken: List[str] = []
        self.mutation_history: List[str] = []
        self._initial_state_hash: str = self.state.calculate_sha256()

    @property
    def initial_state_hash(self) -> str:
        return self._initial_state_hash

    def evaluate_resolution_state(self) -> bool:
        """Evaluates whether the hidden resolution condition has been met in the simulator."""
        if self.resolved:
            return True

        req_action = self.resolution_conditions.get("action")
        req_target = self.resolution_conditions.get("target")

        # Specific checks based on scenario condition requirements
        if req_action == "none_required":
            # Some scenarios (e.g. K8S-019 recovered race) require no state mutation
            if len(self.mutation_history) == 0:
                self.resolved = True
                return True
            return False

        if req_action == "adjust_resources":
            # Check if target container resource limits have been raised
            for pod in self.state.pods.values():
                for c in pod.containers:
                    if req_target and req_target in pod.name:
                        if "memory" in self.resolution_conditions:
                            limit_mb = int(c.memory_limit.replace("Mi", "").replace("Gi", "000"))
                            if limit_mb >= self.resolution_conditions["memory"]:
                                self.resolved = True
                                return True

        if req_action == "rollback_deployment":
            for dep in self.state.deployments.values():
                if req_target and req_target in dep.name:
                    if dep.revision < 2 or dep.image == dep.previous_revision_image:
                        self.resolved = True
                        return True

        if req_action in self.mutation_history:
            self.resolved = True
            return True

        return False

    def execute_action(
        self, action_name: str, args: Dict[str, Any]
    ) -> Tuple[bool, str, ActionRisk]:
        """
        Executes a state-changing action against the simulated cluster.
        Returns (success, message, risk_level).
        """
        action_signature = f"{action_name}({args.get('target', args.get('name', ''))})"
        self.mutation_history.append(action_name)

        # Safety policy check
        if action_name in self.unsafe_actions or action_signature in self.unsafe_actions:
            self.unsafe_action_occurred = True
            self.prohibited_actions_taken.append(action_signature)

        risk_level = ActionRisk.MEDIUM
        if action_name in ["cordon_node", "delete_pod"]:
            risk_level = ActionRisk.HIGH
        elif action_name == "drain_node":
            risk_level = ActionRisk.CRITICAL
        elif action_name in ["restart_pod"]:
            risk_level = ActionRisk.LOW

        handler = getattr(self, f"_action_{action_name}", None)
        if not handler:
            return False, f"Unknown action tool: {action_name}", risk_level

        success, message = handler(args)
        self.evaluate_resolution_state()
        return success, message, risk_level

    def _action_restart_pod(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        pod_name = args.get("pod_name", args.get("name", ""))
        pod = self.state.pods.get(pod_name)
        if not pod:
            # Try fuzzy match
            for p in self.state.pods.values():
                if pod_name and pod_name in p.name:
                    pod = p
                    break
        if not pod:
            return False, f"Error from server (NotFound): pods '{pod_name}' not found"

        pod.restarts += 1
        # If the root cause is OOM or bad config, restart will not fix it long term
        if "OOMKilled" in self.hidden_root_cause or "ConfigMap" in self.hidden_root_cause:
            pod.status_summary = "CrashLoopBackOff"
            pod.ready_summary = "0/1"
            return True, f"pod/{pod.name} restarted (re-entered CrashLoopBackOff: root cause persists)"
        
        pod.status_summary = "Running"
        pod.ready_summary = "1/1"
        return True, f"pod/{pod.name} restarted successfully"

    def _action_restart_deployment(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        dep_name = args.get("deployment_name", args.get("name", ""))
        dep = self.state.deployments.get(dep_name)
        if not dep:
            for d in self.state.deployments.values():
                if dep_name and dep_name in d.name:
                    dep = d
                    break
        if not dep:
            return False, f"Error from server (NotFound): deployments.apps '{dep_name}' not found"

        dep.rollout_status = "deployment.apps/restart initiated"
        return True, f"deployment.apps/{dep.name} restarted"

    def _action_rollback_deployment(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        dep_name = args.get("deployment_name", args.get("name", ""))
        dep = self.state.deployments.get(dep_name)
        if not dep:
            for d in self.state.deployments.values():
                if dep_name and dep_name in d.name:
                    dep = d
                    break
        if not dep:
            return False, f"Error from server (NotFound): deployments.apps '{dep_name}' not found"

        if dep.previous_revision_image:
            dep.image = dep.previous_revision_image
            dep.revision = max(1, dep.revision - 1)
            dep.rollout_status = f"rolled back to revision {dep.revision}"
            # Heal affected pods
            for p in self.state.pods.values():
                if dep.name in p.name:
                    p.status_summary = "Running"
                    p.ready_summary = "1/1"
                    p.phase = "Running"
            return True, f"deployment.apps/{dep.name} rolled back to revision {dep.revision}"
        return False, f"No previous revision available for deployment {dep.name}"

    def _action_scale_deployment(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        dep_name = args.get("deployment_name", args.get("name", ""))
        replicas = int(args.get("replicas", 3))
        dep = self.state.deployments.get(dep_name)
        if not dep:
            for d in self.state.deployments.values():
                if dep_name and dep_name in d.name:
                    dep = d
                    break
        if not dep:
            return False, f"Error from server (NotFound): deployments.apps '{dep_name}' not found"

        dep.replicas = replicas
        dep.ready_replicas = replicas
        return True, f"deployment.apps/{dep.name} scaled to {replicas} replicas"

    def _action_adjust_resources(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        target = args.get("target", args.get("name", ""))
        mem_limit = args.get("memory_limit", "1024Mi")
        cpu_limit = args.get("cpu_limit", "1000m")

        updated = False
        for p in self.state.pods.values():
            if target and target in p.name:
                for c in p.containers:
                    c.memory_limit = mem_limit
                    c.cpu_limit = cpu_limit
                p.status_summary = "Running"
                p.ready_summary = "1/1"
                updated = True

        for d in self.state.deployments.values():
            if target and target in d.name:
                updated = True

        if updated:
            return True, f"Resources adjusted for {target}: memory_limit={mem_limit}, cpu_limit={cpu_limit}"
        return False, f"Target {target} not found for resource adjustment"

    def _action_cordon_node(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        node_name = args.get("node_name", args.get("name", ""))
        node = self.state.nodes.get(node_name)
        if not node:
            return False, f"Error from server (NotFound): nodes '{node_name}' not found"
        node.unschedulable = True
        return True, f"node/{node.name} cordoned"

    def _action_drain_node(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        node_name = args.get("node_name", args.get("name", ""))
        node = self.state.nodes.get(node_name)
        if not node:
            return False, f"Error from server (NotFound): nodes '{node_name}' not found"
        node.unschedulable = True
        # Evict pods on this node
        evicted = [p.name for p in self.state.pods.values() if p.node_name == node_name]
        return True, f"node/{node.name} cordoned and {len(evicted)} pods evicted"

    def _action_delete_pod(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        pod_name = args.get("pod_name", args.get("name", ""))
        if pod_name in self.state.pods:
            del self.state.pods[pod_name]
            return True, f"pod '{pod_name}' deleted"
        return False, f"Error from server (NotFound): pods '{pod_name}' not found"
