#!/usr/bin/env python
# utils/graph_integrity.py

"""
Graph Integrity Checker for Consent Chat Graph

Usage:
    python graph_integrity.py path/to/conversation_graph.json

This script verifies:
- All referenced parent/child IDs exist
- Parent-child relationships are mirrored
- There are no unreachable nodes
- Cycles are detected (excluding test_question nodes)
- Dead-end nodes are marked as terminal (`end_sequence=true`)
"""
import json
import sys

def is_test_question(node_id, graph):
    """
    Returns True if the node has a test_question flag set to true in metadata.
    """
    node = graph.get(node_id, {})
    return str(node.get("metadata", {}).get("test_question", "")).lower() == "true"

def normalize_metadata_flags(metadata):
    """
    Normalize metadata boolean fields to strings 'true' or 'false'.
    """
    for key in ["end_sequence", "test_question"]:
        if key in metadata:
            val = metadata[key]
            if isinstance(val, bool):
                metadata[key] = "true" if val else "false"
            elif isinstance(val, str) and val.lower() in ["true", "false"]:
                metadata[key] = val.lower()
            else:
                metadata[key] = "false"
    return metadata

def trace_cycle(graph, start_node):
    """
    Trace and return the full cycle starting from a node.
    """
    path = []
    visited = set()

    def dfs(node_id):
        if node_id in visited:
            if node_id in path:
                cycle_index = path.index(node_id)
                return path[cycle_index:] + [node_id]
            return None
        visited.add(node_id)
        path.append(node_id)
        for child_id in graph.get(node_id, {}).get("child_ids", []):
            result = dfs(child_id)
            if result:
                return result
        path.pop()
        return None

    return dfs(start_node)

def canonicalize_cycle(cycle):
    """
    Canonicalize the cycle so duplicates can be compared reliably.
    Rotate so the smallest node ID is first.
    """
    if not cycle:
        return ()
    min_index = min(range(len(cycle)), key=lambda i: cycle[i])
    rotated = cycle[min_index:] + cycle[:min_index]
    return tuple(rotated)

def check_graph_integrity(graph):
    """
    Perform integrity checks on the graph: missing fields, bad links, unreachable or cyclic nodes.
    """
    errors = []
    all_node_ids = set(graph.keys())
    seen = set()

    for node in graph.values():
        if "metadata" in node:
            node["metadata"] = normalize_metadata_flags(node["metadata"])

    for node_id, node in graph.items():
        required_fields = ['type', 'messages', 'parent_ids', 'child_ids', 'metadata']
        for field in required_fields:
            if field not in node:
                errors.append(f"Missing field '{field}' in node: {node_id}")

        for pid in node.get("parent_ids", []):
            if pid not in all_node_ids:
                errors.append(f"{node_id} has non-existent parent_id: {pid}")
        for cid in node.get("child_ids", []):
            if cid not in all_node_ids:
                errors.append(f"{node_id} has non-existent child_id: {cid}")

        for cid in node.get("child_ids", []):
            child = graph.get(cid)
            if child and node_id not in child.get("parent_ids", []):
                errors.append(f"Inconsistent link: {node_id} -> {cid} not mirrored")
        for pid in node.get("parent_ids", []):
            parent = graph.get(pid)
            if parent and node_id not in parent.get("child_ids", []):
                errors.append(f"Inconsistent link: {node_id} <- {pid} not mirrored")

        seen.add(node_id)

    start_nodes = [nid for nid, n in graph.items() if "start" in n.get("parent_ids", [])]
    if not start_nodes:
        errors.append("No start node found (parent_ids = ['start'])")
        return report(errors, graph)

    visited = set()
    seen_cycles = set()

    def dfs(nid, path):
        if nid in path:
            cycle = trace_cycle(graph, nid)
            if cycle:
                canon = canonicalize_cycle(cycle)
                if canon not in seen_cycles:
                    seen_cycles.add(canon)
        if nid in visited:
            return
        visited.add(nid)
        path.add(nid)
        for child_id in graph[nid].get("child_ids", []):
            dfs(child_id, path)
        path.remove(nid)

    for start in start_nodes:
        dfs(start, set())

    unreachable = all_node_ids - visited
    for nid in unreachable:
        if nid != "start":
            errors.append(f"Node {nid} is unreachable from start")

    for cycle in seen_cycles:
        errors.append(f"Cycle detected: {' -> '.join(cycle)}")

    for nid in visited:
        node = graph[nid]
        if not node.get("child_ids") and node.get("metadata", {}).get("end_sequence") != "true":
            errors.append(f"Dead-end node {nid} is not marked terminal")

    return report(errors, graph)

def report(errors, graph):
    """
    Print summary and list of integrity issues.
    """
    print(f"\n✅ Checked {len(graph)} nodes.")
    if errors:
        print(f"❌ Found {len(errors)} issues:")
        for err in errors:
            print(" -", err)
        return 1
    else:
        print("🎉 No integrity issues found!")
        return 0

def main():
    """
    CLI entry point.
    """
    if len(sys.argv) != 2:
        print("Usage: python graph_integrity.py path/to/graph.json")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        with open(file_path, "r") as f:
            graph = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        sys.exit(1)

    exit_code = check_graph_integrity(graph)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
