# Mistake Notebook Skill Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve `mistake-notebook` trigger accuracy first, while also rewriting the skill into a shorter, more reliable workflow guide.

**Architecture:** Replace the current long, mixed-purpose `SKILL.md` with a leaner workflow-oriented skill. Keep `README.md` and auxiliary docs as reference material, but make `SKILL.md` focus on trigger boundaries, decision flow, critical rules, and response patterns. Reuse the existing trigger-eval dataset and `skill-creator` tooling to validate and refine the new description.

**Tech Stack:** Markdown skill files, HTML trigger eval review asset, PowerShell via `claude.ps1`, Python helper scripts from `skill-creator`

---

### Task 1: Restructure the skill document

**Files:**
- Modify: `SKILL.md`
- Reference: `README.md`
- Reference: `reference.md` (previously `SKILL-DEV.md`)

**Step 1: Snapshot the current skill content**

Read the current `SKILL.md` and identify sections that belong in the triggering skill versus sections that belong in supporting documentation.

**Step 2: Draft the new frontmatter description**

Write a more aggressive trigger description that:
- Names the core workflow clearly
- Includes concrete trigger phrases, file paths, and script names
- Explicitly names near-miss cases that should not trigger

**Step 3: Rewrite the body as a workflow guide**

Keep only:
- When to use / when not to use
- Core decision flow by user intent
- Critical behavioral rules
- Minimal output patterns
- References to existing docs for deep implementation detail

**Step 4: Check for consistency**

Verify the rewritten `SKILL.md` no longer contradicts the current PDF-first workflow and no longer uses unwanted strong persona language.

---

### Task 2: Formalize trigger evaluation inputs

**Files:**
- Create: `trigger-optimization/eval_set.json`
- Modify: `trigger-optimization/eval_review.html` (only if needed)

**Step 1: Extract the embedded eval set**

Take the current query set embedded in `trigger-optimization/eval_review.html` and save it as a standalone JSON file.

**Step 2: Review for coverage**

Confirm the set still covers:
- positive cases for intake, review, export, analysis, reminders, updates, schema questions
- negative near-misses like single-question tutoring, Anki, general study plans, spreadsheets, OCR, unrelated development

**Step 3: Keep the eval review asset aligned**

Update the displayed current description in the review HTML if the rewritten description changes materially.

---

### Task 3: Run trigger optimization and inspect results

**Files:**
- Use: `trigger-optimization/eval_set.json`
- Modify: `SKILL.md`
- Output: `trigger-optimization/` artifacts created by the optimization loop

**Step 1: Verify the CLI path**

Confirm `claude.ps1` is callable from PowerShell in this workspace.

**Step 2: Run the optimization loop**

Use the `skill-creator` tooling to run the description optimization loop against the standalone eval set.

**Step 3: Compare candidate descriptions**

Inspect the reported scores and compare the best generated description with the manually drafted one.

**Step 4: Apply the best result with judgment**

Update `SKILL.md` with the final chosen description, preferring generalizable trigger coverage over overfitting to the eval set.

---

### Task 4: Verify and summarize

**Files:**
- Check: `SKILL.md`
- Check: `trigger-optimization/eval_set.json`
- Check: optimization outputs

**Step 1: Sanity-check formatting**

Ensure `SKILL.md` remains readable and valid markdown, and the eval JSON is valid.

**Step 2: Run lint/diagnostic check if relevant**

Use IDE diagnostics for edited files and fix any introduced problems.

**Step 3: Summarize outcomes**

Report:
- what changed in the skill structure
- the final description direction
- whether optimization tooling ran successfully
- any follow-up options, such as packaging the skill
