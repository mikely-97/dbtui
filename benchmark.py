#!/usr/bin/env python3
"""
Benchmark script for dbtui performance testing.
Run with: python benchmark.py <path_to_dbt_project>
"""

import sys
import time
from pathlib import Path


def benchmark_project_load(project_path: str):
    """Benchmark project loading and model operations."""
    from dbtui.backend.project import DbtProject

    print(f"Benchmarking with project: {project_path}")
    print("=" * 60)

    # 1. Project loading (metrics are collected automatically)
    project = DbtProject(project_path)

    # Print built-in metrics
    if project.load_metrics:
        m = project.load_metrics
        print(f"Project load time: {m.total_load_ms:.1f}ms ({m.model_count} models)")
        print(f"  - parse_dbt_project.yml: {m.parse_dbt_project_yml_ms:.1f}ms")
        print(f"  - load_models: {m.load_models_ms:.1f}ms")
        print(f"  - populate_graph: {m.populate_graph_ms:.1f}ms")
        print(f"  - collect_property_claims: {m.collect_property_claims_ms:.1f}ms")

    print("-" * 60)

    # 2. Accessing all model names
    start = time.perf_counter()
    names = [m.name for m in project.models]
    name_access_time = (time.perf_counter() - start) * 1000
    print(f"All model names access: {name_access_time:.1f}ms")

    # 3. Accessing parents for all models
    start = time.perf_counter()
    all_parents = [m.parents for m in project.models]
    parents_time = (time.perf_counter() - start) * 1000
    print(f"All parents access: {parents_time:.1f}ms")

    # 4. Accessing children for all models
    start = time.perf_counter()
    all_children = [m.children for m in project.models]
    children_time = (time.perf_counter() - start) * 1000
    print(f"All children access: {children_time:.1f}ms")

    # 5. Model search performance
    if names:
        test_name = names[len(names)//2][:3]
        start = time.perf_counter()
        results = project.search_model(test_name)
        search_time = (time.perf_counter() - start) * 1000
        print(f"Model search ('{test_name}'): {search_time:.1f}ms ({len(results)} results)")

    print("=" * 60)

    return project.load_metrics


if __name__ == '__main__':
    if len(sys.argv) < 2:
        project_path = Path.home() / 'Documents/grimoires/coem_bi'
    else:
        project_path = sys.argv[1]

    benchmark_project_load(str(project_path))
