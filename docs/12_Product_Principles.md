# SATCO Product Principles

## Purpose

This document establishes the permanent principles used to evaluate SATCO product decisions. The principles translate the Product Vision and Engineering Copilot architecture into durable decision rules.

## Scope

These principles apply to every future capability, workflow, user experience, AI behavior, and product-governance decision. They do not prescribe implementation.

## Definitions

- **Principle:** A durable rule that guides decisions across changing features and technologies.
- **Engineering value:** A demonstrable improvement in engineering understanding, decision quality, risk control, readiness, or organizational learning.
- **Recommendation:** Advisory guidance that requires human evaluation.
- **Traceability:** The ability to understand the context, evidence, reasoning, review, and outcome associated with a recommendation or decision.

## Permanent Product Principles

1. **Engineering First.** Product priorities begin with genuine engineering work and responsibility.
2. **Engineers Decide.** SATCO may suggest, analyze, and warn; accountable engineers make engineering decisions.
3. **Human Responsibility Is Permanent.** Product maturity must never erase professional accountability.
4. **Context Before AI.** AI may advise only after relevant project and engineering context is understood.
5. **Engineering Context Is More Valuable Than Prompt Quality.** Product quality must not depend on users learning conversational tricks.
6. **AI Explains Before It Recommends.** A recommendation must be preceded by a clear account of the observation and its significance.
7. **Never Invent Engineering Facts.** Unknown information remains unknown and is identified as such.
8. **Never Hide Engineering Uncertainty.** Confidence, assumptions, gaps, and limitations must be visible.
9. **Trust Before Automation.** Reliable, reviewable assistance is more valuable than unaccountable autonomy.
10. **Transparency Before Intelligence.** Users must be able to understand why an insight exists before being asked to rely on it.
11. **Every Recommendation Must Be Traceable.** Relevant context, evidence, standards, assumptions, and history must be discoverable.
12. **Recommendations Are Not Decisions.** AI output must remain distinguishable from reviewed human conclusions.
13. **Review Before Reliance.** Material engineering advice requires appropriate human review before operational use.
14. **Never Surprise Engineers.** Significant changes, assumptions, conflicts, and impacts must be surfaced clearly.
15. **Missing Information Is a Result.** Identifying an important absence can be more valuable than producing a speculative answer.
16. **Confidence Must Be Earned.** Confidence reflects evidence and context quality, not linguistic certainty.
17. **Standards Require Context.** A standard is relevant only when applicability, edition, jurisdiction, and project obligations are understood.
18. **Similarity Is Evidence, Not Equivalence.** Historical projects may inform judgment but never substitute for current-project analysis.
19. **Relationships Create Engineering Meaning.** Objects become useful when their dependencies, revisions, decisions, and consequences are visible.
20. **Workspace Before Conversation.** Engineering information belongs in governed Engineering Workspaces, not isolated chat histories.
21. **Decisions Preserve Rationale.** A decision without its basis, owner, time, and affected context is incomplete.
22. **Memory Follows Review.** Only governed outcomes and lessons may become trusted Engineering Memory.
23. **Every Feature Must Improve Engineering Decisions.** Features without a clear decision or understanding benefit do not belong.
24. **Every Feature Must Reduce Engineering Risk.** Value must include earlier detection, clearer ownership, stronger evidence, or reduced uncertainty.
25. **Impact Must Cross Boundaries.** Changes should be considered across disciplines, documents, equipment, lifecycle stages, and prior decisions.
26. **Consistency Over Complexity.** Shared concepts and predictable behavior are preferred to fragmented sophistication.
27. **Product Simplicity Is a Competitive Advantage.** The product should minimize operational friction while preserving necessary engineering depth.
28. **Progressive Disclosure Protects Attention.** Present the most relevant engineering information first and reveal detail when needed.
29. **Safety Boundaries Are Product Features.** Refusal, escalation, and limitations are essential behavior, not exceptional failure.
30. **Continuous Improvement Must Remain Governed.** SATCO learns from reviewed outcomes without silently changing engineering truth.

## Principle Application

Principles are applied together. A capability that is explainable but lacks relevant context is not acceptable. A feature that saves clicks but obscures uncertainty is not acceptable. Apparent tension between principles must be resolved in favor of engineering safety, human responsibility, and traceability.

When evaluating a proposal, reviewers should ask:

- What engineering problem does it solve?
- Which decision, risk, or readiness outcome improves?
- What context and evidence does it require?
- How are uncertainty and limitations shown?
- Where does human review occur?
- What becomes part of Engineering Memory, and under what governance?

## Design Rules

- Use advisory terms such as **Suggested**, **Recommended**, **Potential issue**, and **Needs review** for AI output.
- Do not label AI output **Final**, **Approved**, or equivalent.
- Keep facts, assumptions, recommendations, decisions, and approved records visibly distinct.
- Provide a path from every material insight to its supporting context.
- Prefer coherent workspace behavior over standalone AI features.
- Reject convenience that weakens review, ownership, or traceability.

## Examples

**Acceptable:** SATCO identifies a potential inconsistency between an equipment requirement and a reviewed document, explains the relationship, states confidence, and requests discipline review.

**Unacceptable:** SATCO silently resolves the inconsistency, updates the approved conclusion, or presents a single answer as final.

**Acceptable:** SATCO suggests a historical project and explains comparable scope, standards, and key differences.

**Unacceptable:** SATCO copies a prior decision because the projects share a category.

## Future Implications

Every future PATCH must identify the principles it advances and demonstrate that it violates none. Product reviews should treat these principles as acceptance criteria, especially where AI behavior, engineering responsibility, uncertainty, review, or memory are affected.
