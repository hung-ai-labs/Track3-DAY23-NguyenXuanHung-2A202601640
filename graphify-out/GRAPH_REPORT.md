# Graph Report - .  (2026-08-25)

## Corpus Check
- Corpus is ~5,861 words - fits in a single context window. You may not need a graph.

## Summary
- 163 nodes · 258 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Graph State and Persistence
- CLI Metrics and Reporting
- Workflow Node Logic
- Conditional Routing
- Grading and Evidence
- Lab Architecture Requirements
- Audit Event Models
- LLM Provider Factory
- CI Quality Gates
- Package Interface
- Project Package

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 22 edges
2. `run_scenarios()` - 13 edges
3. `Scenario` - 10 edges
4. `initial_state()` - 10 edges
5. `route_after_classify()` - 9 edges
6. `MetricsReport` - 8 edges
7. `metric_from_state()` - 8 edges
8. `build_graph()` - 7 edges
9. `build_checkpointer()` - 7 edges
10. `write_report()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Retry and Dead-Letter Flow` --semantically_similar_to--> `Bounded Retry Loop`  [INFERRED] [semantically similar]
  docs/LAB_GUIDE.md → README.md
- `Risky Action Approval Flow` --semantically_similar_to--> `Human-in-the-Loop Approval`  [INFERRED] [semantically similar]
  docs/LAB_GUIDE.md → README.md
- `SQLite Checkpointing` --implements--> `Checkpoint Persistence and Recovery`  [INFERRED]
  docs/LAB_GUIDE.md → README.md
- `Metrics Report Specification` --semantically_similar_to--> `Metrics and Scenario Validation`  [INFERRED] [semantically similar]
  docs/METRICS.md → README.md
- `PostgreSQL 16 Service` --conceptually_related_to--> `Checkpoint Persistence and Recovery`  [INFERRED]
  docker-compose.yml → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Support-Ticket Graph Core Mechanisms** — readme_typed_serializable_agent_state, readme_llm_structured_intent_classification, readme_grounded_llm_answer_generation, readme_bounded_retry_loop, readme_human_in_the_loop_approval, readme_checkpoint_persistence_and_recovery [EXTRACTED 1.00]
- **Target Graph Route Flows** — docs_lab_guide_target_graph, docs_lab_guide_conditional_routing, docs_lab_guide_retry_and_dead_letter_flow, docs_lab_guide_risky_action_approval_flow [EXTRACTED 1.00]
- **Lab Report Evidence Sections** — reports_lab_report_template_architecture_and_state_evidence, reports_lab_report_template_scenario_and_failure_evidence, reports_lab_report_template_persistence_and_extension_evidence [EXTRACTED 1.00]

## Communities (11 total, 2 thin omitted)

### Community 0 - "Graph State and Persistence"
Cohesion: 0.10
Nodes (26): field_validator, parametrize, build_graph(), Any, Graph construction. This module is intentionally import-safe. It imports…, Build and compile the LangGraph workflow. TODO(student): Build the complete…, build_checkpointer(), Any (+18 more)

### Community 1 - "CLI Metrics and Reporting"
Cohesion: 0.13
Nodes (25): command, Option, Path, Run all grading scenarios and write metrics JSON., Validate metrics JSON schema for grading., run_scenarios(), validate_metrics(), metric_from_state() (+17 more)

### Community 2 - "Workflow Node Logic"
Cohesion: 0.11
Nodes (26): answer_node(), approval_node(), ask_clarification_node(), classify_node(), dead_letter_node(), evaluate_node(), finalize_node(), intake_node() (+18 more)

### Community 3 - "Conditional Routing"
Cohesion: 0.12
Nodes (23): Routing functions for conditional edges. Each function takes AgentState and…, Map classified route to the next graph node. Mapping: - "simple" → "answer" -…, Decide if tool result is satisfactory or needs retry. This is the 'done?' check…, Decide whether to retry the tool or give up. MUST be bounded — unbounded retry…, Route based on human approval decision. - If approved → "tool" (proceed with…, route_after_approval(), route_after_classify(), route_after_evaluate() (+15 more)

### Community 4 - "Grading and Evidence"
Cohesion: 0.14
Nodes (16): Hidden Grading Configuration, In-Memory Checkpointer, In-Memory Checkpointer, Sample Lab Configuration, PostgreSQL Health Check, PostgreSQL 16 Service, Metrics Report Specification, Recovery Evidence Metric (+8 more)

### Community 5 - "Lab Architecture Requirements"
Cohesion: 0.14
Nodes (16): Conditional Routing, Retry and Dead-Letter Flow, Risky Action Approval Flow, SQLite Checkpointing, Target Agent Graph, Grading Rubric, LLM Integration Criteria, Production-Quality Grade Band (+8 more)

### Community 6 - "Audit Event Models"
Cohesion: 0.29
Nodes (7): ApprovalDecision, LabEvent, make_event(), Any, BaseModel, Create a normalized event payload., Append-only audit event for grading and debugging.

### Community 7 - "LLM Provider Factory"
Cohesion: 0.50
Nodes (3): get_llm(), LLM factory helper. Provides a simple interface to create LLM clients for use…, Create an LLM client from environment configuration. Checks for API keys in…

### Community 8 - "CI Quality Gates"
Cohesion: 0.67
Nodes (3): CI Workflow, Lint and Test Gates, Python 3.11 Test Environment

## Knowledge Gaps
- **8 isolated node(s):** `day08-langgraph-agent-lab`, `Python 3.11 Test Environment`, `LangGraph Agentic Orchestration Lab`, `Typed Serializable Agent State`, `PostgreSQL Health Check` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentState` connect `Workflow Node Logic` to `Graph State and Persistence`, `Conditional Routing`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Why does `initial_state()` connect `Graph State and Persistence` to `CLI Metrics and Reporting`, `Workflow Node Logic`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `run_scenarios()` connect `CLI Metrics and Reporting` to `Graph State and Persistence`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **What connects `day08-langgraph-agent-lab`, `Python 3.11 Test Environment`, `LangGraph Agentic Orchestration Lab` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Graph State and Persistence` be split into smaller, more focused modules?**
  _Cohesion score 0.09659090909090909 - nodes in this community are weakly interconnected._
- **Should `CLI Metrics and Reporting` be split into smaller, more focused modules?**
  _Cohesion score 0.1330049261083744 - nodes in this community are weakly interconnected._
- **Should `Workflow Node Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.10541310541310542 - nodes in this community are weakly interconnected._