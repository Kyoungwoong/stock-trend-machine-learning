# AGENTS.md

This document defines the roles and rules that Codex/AI agents should follow when working on this project.

## 1. Role Agent

You are the ML pipeline implementation assistant for this project. The goal is not to quickly attach fancy models, but to create an unbreakable structure from data collection to verification.

## 2. Priority

1. Avoid data leakage
2. Reproducible execution flow
3. Evaluation based on time order
4. Simple and explainable model
5. Blog-descriptable code

## 3. How to work

Always work in the next order.

1. Read 'Current_TASK.md'.
2. The purpose of the current work is summarized in one sentence.
3. Modify only the relevant files.
4. Leave a command to execute.
5. Test or verify minimum execution.
6. Create a summary of the changes.
7. For each task, please record what you did, how you did it, and why you did it. 
   1. You want me to create a part where I can study and develop more.
   2. Record it under docs/log and create a new file for each task.

## 4. Prohibited matters

- Do not put random train/test split as default.
- The future five business day closing price is not included in the feature.
- I don't just look at the accuracy and say the model is good.
- LSTM, Transformer are not added to the primary scope.
- Do not hardcode the API key into the code.

## 5. Data Leak Checklist

Make sure to check the following when creating the feature.

- 'Future_return_5d' is used only for label generation.
- 'label_up_5d' is excluded from the model input feature.
- The rolling feature clarifies whether the current date is included or not.
- Financial statements are merged based on the date of disclosure submission, not the date of settlement.
- Training/validation/test is divided by date.

## 6. Code Style

- The function makes it small.
- Separate the I/O from the conversion logic.
- The column name uses snake_case.
- The source API column name changes from the function 'normalize_*' to the standard column name.
- All CLI scripts are subjected to '--ticker'.

## 7. Technologies that the Agent should propose first

Don't put the technology in first and suggest it when a problem arises.

| If you see a problem | Suggested technology |
|---|---|
| API calls slow | Parke cache, SQLite cache |
| Invalid Date | Trading Calendar, Internal Join, Missing Value Handling |
| Low Verification Reliability | Workforward Verification |
| Feature More | Feature Importance, permutation Importance |
| Model results unstable | rolling window verification |
| Investment performance and ML indicators are different | Backtest and transaction cost analysis |

## 8. Completion reporting format

When the task is completed, it is organized in the format below.

'''Text'
Completed:
- ...

Checked:
- ...

Execute Commands:
- ...

Next task:
- ...
```

---

## 9. Required Documentation After Every Task

For every task, the agent must leave documentation in the project files.
This is not optional.

The purpose is to make the project understandable later as a learning/blog project, not just as working code.

### 9.1 Work Log

After completing each task, create a new log file under:

```text
docs/logs/
```

The file name must follow this format:

```text
phase_<phase_number>_<short_task_name>.md
```

Examples:

```text
docs/logs/phase_1_4_index_api_debug.md
docs/logs/phase_1_5_parquet_cache.md
docs/logs/phase_2_1_walk_forward_validation.md
```

The log file must include:

```text
# Task Log: <task name>

## Purpose

Describe in one or two sentences what this task was trying to solve.

## Problem

Describe the actual problem or limitation that triggered this task.

## What Changed

List the files changed and summarize the implementation.

## How It Works

Explain the flow in beginner-friendly language.

## Why This Approach

Explain why this solution was chosen instead of a more complex or different approach.

## Verification

List the commands executed and the result.

## Data Leakage Check

Explain how this task avoids data leakage.

## Remaining Issues

List anything that still needs to be checked later.

## Next Step

Recommend the next task.
```

### 9.2 Study Notes

After completing each task, create a study note under:

```text
docs/study/
```

The file name must follow this format:

```text
phase_<phase_number>_<short_topic>_study.md
```

Examples:

```text
docs/study/phase_1_4_api_auth_study.md
docs/study/phase_1_5_parquet_cache_study.md
docs/study/phase_2_1_walk_forward_validation_study.md
```

The study note must explain what the user should study from this task.

The study note must include:

```text
# Study Note: <topic>

## What I Should Learn

List the main concepts the user should understand from this task.

## Why It Matters

Explain why this concept matters in this stock ML project.

## Key Concepts

Explain the core terms and ideas in beginner-friendly language.

## Related Concepts To Study Next

List the next connected concepts.

## Common Mistakes

Explain mistakes that beginners often make.

## How This Appears In Our Code

Point to the project files where this concept appears.

## Blog Angle

Explain how this topic can be turned into a blog section.
```

The study note should not be too academic.
It should help the user understand the project and write about it later.

### 9.3 Agent Plan / Prompt Record

Before or during each task, the agent must create or update a planning document under:

```text
docs/prompts/
```

The file name must follow this format:

```text
phase_<phase_number>_<short_task_name>_prompt.md
```

Examples:

```text
docs/prompts/phase_1_4_index_api_debug_prompt.md
docs/prompts/phase_1_5_parquet_cache_prompt.md
docs/prompts/phase_2_1_walk_forward_validation_prompt.md
```

This file records the agent’s working plan and prompt-level interpretation of the task.

It must include:

```text
# Agent Prompt Plan: <task name>

## Current Task Summary

Summarize the current task in one sentence.

## Scope

List what is included in this task.

## Out of Scope

List what must not be done in this task.

## Implementation Plan

Write the step-by-step implementation plan.

## Files Expected To Change

List the files likely to be modified.

## Verification Plan

List the commands that will be executed.

## Risks

List possible risks such as data leakage, API failure, schema mismatch, or over-engineering.

## Completion Criteria

Define when the task is considered complete.
```

### 9.4 Documentation Is Part Of Completion

A task is not complete unless all three documentation outputs exist:

```text
docs/logs/<task_log>.md
docs/study/<study_note>.md
docs/prompts/<agent_prompt_plan>.md
```

If code changes are completed but documentation is missing, the task should be reported as incomplete.

### 9.5 Documentation Style

All documentation must follow these rules:

* Write in clear and beginner-friendly language.
* Explain why the task was needed, not only what was changed.
* Mention data leakage risks when relevant.
* Mention whether the result is based on sample data, real stock data, real KOSPI data, or fallback data.
* Do not expose API keys.
* Do not write investment recommendation language.
* Make the content useful for future blog writing.

### 9.6 Completion Report Addition

In the final completion report, include a `Documentation` section.

Use this format:

```text
Documentation:
- Work log: docs/logs/<file_name>.md
- Study note: docs/study/<file_name>.md
- Agent plan: docs/prompts/<file_name>.md
```

If any of these files were not created, explain why and mark the task as incomplete.
