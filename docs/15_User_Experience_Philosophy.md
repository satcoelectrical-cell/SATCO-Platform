# SATCO User Experience Philosophy

## Purpose

This document defines how engineers should experience SATCO. It establishes permanent experience principles that keep the product focused on engineering work, context, trust, and review.

## Scope

The philosophy applies to all product surfaces, workflows, information views, AI interactions, notifications, dashboards, and review experiences. It does not prescribe visual designs or implementation.

## Definitions

- **Problem-oriented UX:** An experience organized around engineering questions, risks, decisions, and work outcomes.
- **Workspace-first UX:** An experience in which Engineering Workspaces are the primary home of discipline work and context.
- **Context-first UX:** An experience that makes relevant scope, relationships, revisions, and authority visible before action or recommendation.
- **Progressive disclosure:** Presenting essential information first while keeping supporting depth available.
- **Review-first UX:** An experience designed to help responsible people evaluate evidence and make decisions.

## Desired Engineering Experience

An engineer should enter SATCO and quickly understand:

- where they are in the project and lifecycle;
- which discipline and engineering context are active;
- what requires attention;
- what information is missing or conflicting;
- what has changed;
- which decisions and reviews are open;
- why an AI insight was raised;
- what the recommended next step is;
- who remains responsible for the decision.

The product should reduce the effort required to reconstruct context. It should not reduce engineering work to a stream of messages or generic tasks.

## Problem-Oriented UX

SATCO should organize attention around real engineering needs:

- resolving an inconsistency;
- evaluating a change;
- preparing a review;
- identifying missing inputs;
- understanding readiness;
- deciding the next engineering action;
- tracing the basis of a prior decision.

Features and navigation should serve these outcomes. The product must not force engineers to translate their work into artificial conversational or administrative structures.

## Workspace-First UX

Engineering Workspaces are the primary experience. They contain engineering information, not AI conversations.

A workspace should bring together the active discipline’s:

- scope and context;
- connected systems, equipment, tags, and documents;
- calculations and standards;
- risks, reviews, and decisions;
- execution-plan activities;
- readiness and Engineering Health;
- contextual AI insights.

Cross-discipline relationships should be visible without dissolving discipline accountability.

## Context-First UX

Before presenting or acting on a recommendation, SATCO should show enough context for the engineer to assess relevance. This includes customer, project, plant, area, discipline, system, equipment, tag, document revision, project stage, and prior decisions when material.

The interface should make context changes obvious. Engineers must not unknowingly carry assumptions from one project, area, revision, or discipline into another.

## AI Beside Engineering

AI should appear beside the engineering work it is helping to interpret. Insights about equipment should be available in that equipment context. Revision risks should appear with the affected revision and relationships. Execution-plan recommendations should appear with the relevant workspace and readiness state.

AI must not dominate the experience. The engineering object, evidence, and human decision remain primary.

SATCO is not a ChatGPT-style product. A conversational interaction may be useful as a supporting method, but it must not become the product’s organizing model or an ungoverned substitute for Engineering Workspaces.

## Minimal Clicks with Preserved Meaning

SATCO should minimize unnecessary navigation, repeated entry, and context switching. Fewer interactions are valuable when they reduce friction without hiding engineering consequence.

The product should never remove a confirmation, review, explanation, or context boundary merely to reduce click count. Efficiency is measured by the engineer’s path to understanding and responsible action, not by interaction count alone.

## Progressive Disclosure

The first view should communicate the engineering issue, its importance, confidence, and required action. Supporting relationships, evidence, revision history, assumptions, and reasoning should remain immediately available.

Progressive disclosure should protect attention while preserving auditability. It must not bury uncertainty, safety concerns, or mandatory review.

## Review-First and Explain-First

Every material recommendation should be designed for evaluation. The engineer should be able to:

- understand the observation and implication;
- inspect supporting context and evidence;
- see confidence and missing information;
- compare alternatives;
- accept, revise, reject, or defer;
- record rationale and responsibility.

Explanation must precede acceptance. A prominent action must not be easier to use than understanding its consequence.

## Trust-First UX

Trust is built through consistent behavior:

- AI output is clearly labeled;
- facts and assumptions are distinct;
- uncertainty is visible;
- sources and revisions can be inspected;
- changes are not silent;
- decisions remain attributed to people;
- limitations and refusals are understandable;
- similar situations are handled consistently.

The product should not use urgency, authority cues, or visual prominence to pressure acceptance of AI advice.

## Engineering Dashboard

The Engineering Dashboard should summarize the project’s engineering condition, not merely activity volume. It should orient users to:

- execution-plan progress and changes;
- Engineering Health dimensions;
- missing and late inputs;
- important cross-discipline dependencies;
- unresolved risks and conflicts;
- open reviews and decisions;
- readiness for the next engineering stage or client review;
- recommended areas of attention.

Summary indicators must lead to their underlying evidence and must not imply certainty beyond available context.

## AI Insights Panel

The AI Insights Panel should provide contextual, reviewable assistance. Each insight should communicate:

- type: suggestion, recommendation, potential issue, or needs review;
- affected engineering context;
- why it matters;
- confidence and limitations;
- evidence and relationships;
- recommended next step;
- review status and ownership.

Insights should be prioritized by engineering consequence and relevance, not novelty or engagement.

## Design Rules

1. Begin with the engineer’s problem, not the AI capability.
2. Keep the active project, workspace, and revision context unmistakable.
3. Place intelligence near the engineering object it concerns.
4. Make important missing information more visible than speculative completion.
5. Distinguish AI advice from human decisions through language and presentation.
6. Provide direct access from summaries to evidence and relationships.
7. Use progressive disclosure without hiding risk or uncertainty.
8. Minimize navigation and repeated work, not governance.
9. Support multidisciplinary awareness while preserving accountable ownership.
10. Design every material recommendation for review, explanation, and traceability.
11. Avoid conversational interfaces as the primary information architecture.
12. Prefer calm, consistent signals over attention-seeking behavior.

## Examples

### Potential Conflict

An engineer sees a **Potential issue** in the relevant workspace. The first view explains the possible conflict and affected work. The engineer can then inspect both revisions, their authority, related decisions, and the requested reviewers without leaving the problem context.

### Readiness

A workspace indicates that client-review readiness is limited by missing vendor data and an open calculation review. The score links to these causes and does not present readiness as a final approval.

### Similar Project

SATCO suggests a historical analogue within the current decision context. Similarities, differences, confidence, and the reviewed lesson are visible before the engineer chooses whether it is relevant.

## Future Implications

Future UX proposals must demonstrate how they reduce engineering friction while strengthening context, review, understanding, and trust. Engagement metrics must not override engineering value, and new AI interaction patterns must remain subordinate to the workspace-first product architecture.
