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