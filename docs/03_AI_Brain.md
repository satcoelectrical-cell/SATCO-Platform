# SATCO AI Brain

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# Purpose

SATCO AI Brain is the intelligence layer of SATCO Platform.

Its responsibility is NOT to replace engineers.

Its responsibility is to help engineers think faster, review better and execute projects with higher quality.

---

# Responsibilities

The AI Brain can:

- Analyze engineering projects
- Review engineering documents
- Detect missing information
- Build engineering roadmaps
- Generate engineering checklists
- Assist PLC programming
- Assist Instrumentation Engineering
- Assist Electrical Engineering
- Assist Commissioning
- Assist Troubleshooting

The AI Brain never performs final engineering approval.

---

# AI Brain Components

## 1. Context Builder

Collects every piece of information related to the current project.

Sources include:

- Customer
- Company
- Project
- Uploaded Documents
- Engineering Standards
- Previous Analyses
- Previous AI Responses
- Knowledge Base

Output:

Engineering Context

---

## 2. Prompt Builder

Converts engineering context into professional prompts.

Responsibilities:

- Select prompt template
- Inject project context
- Inject engineering rules
- Build final prompt

Output:

Prompt

---

## 3. AI Router

Determines:

- Which AI provider should be used
- Which model should be used
- Retry policy
- Cost optimization

Current Provider:

OpenAI

Future Providers:

Azure OpenAI
Anthropic
Google Gemini
Local Models

---

## 4. Engineering Analyzer

Receives AI response.

Performs:

- Validation
- Consistency Check
- Risk Detection
- Engineering Review

Stores results into PostgreSQL.

---

## 5. Knowledge Manager

Stores reusable engineering knowledge.

Examples:

Lessons Learned

Best Practices

Engineering Standards

Successful Project Experience

Prompt Improvements

---

## 6. Planner

Builds engineering execution plans.

Examples:

Commissioning Roadmap

FAT Checklist

SAT Checklist

PLC Development Plan

Engineering Milestones

---

## 7. Reviewer

Reviews:

PLC Programs

Engineering Documents

Instrument Index

IO List

Electrical Drawings

Cause & Effect

Loop Diagrams

Cable Schedule

---

# AI Workflow

Project Created

↓

Collect Context

↓

Build Prompt

↓

Call AI

↓

Validate Response

↓

Store Result

↓

Generate Tasks

↓

Notify Engineer

---

# Engineering Philosophy

AI assists.

Engineer decides.

Knowledge belongs to SATCO.

---

END OF AI BRAIN
