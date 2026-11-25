# AI Usage Disclosure

## Tools used

- Tool and version: Claude (Anthropic), model Claude Sonnet 5.5, used in the Claude app (Claude Code environment). No other AI tools were used.

## Conversation links

- Link 1: <https://claude.ai/share/4e56a3b9-05a6-448a-bc5d-5e73b018e4ea>
- Link 2: (none)

## What I used them for

- Explaining the assignment: what to implement, the order of the checks, and the logging, CLI and query rules.
- Getting a plan and hints for `validator.py` (ASCII-only regex with `fullmatch`, strict datetime format, finite price check). I wrote the code myself.
- Reviewing my code and testing it against the sample data in `data/` and the public test script.
- Adding comments in simple English to `validator.py`, because English is not my first language.
- Finding a bug in my `csv_loader.py` and fixing it (see the table).
- Reviewing `flight_parser.py` and running it for edge cases (exit codes, usage errors, log handler cleanup).

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| validator.py | whole file | I wrote the code. Claude explained the plan and the pitfalls beforehand, reviewed the result, and added code comments (no logic changes). |
| csv_loader.py | `parse_files`, the file reading loop | My first version used `csv.reader` on the whole file. Claude found that an unclosed quote can swallow the following lines and break line numbers, and wrote the replacement loop (read line by line, skip blank and comment lines first, parse one line at a time). The duplicate check and the error message format are mine. |
| flight_parser.py | whole file | I wrote the code. Claude only reviewed it and ran tests; no code changes by Claude. |
| query.py | `run_query`, `run_queries` | <FILL IN: write "written by me" or describe any AI help> |

## Key prompts

1. "i have this assignment, explain the things i have to do, i will do it my own"
2. "lets do validator" / "i did it my own hows this. and can u add necessary comments my english is not good"
3. "next is this how to do explain" (for `csv_loader.py`), then I sent my code for review.
4. I sent `flight_parser.py` for review.

## What I changed or verified myself

- Wrote `validator.py` and `flight_parser.py` myself and the first version of `csv_loader.py`.
- Ran the public tests (`python tests/run_public_tests.py`) and checked the sample outputs against the expected errors in the assignment.
- Tested my own edge cases: non-ASCII letters, `2025-1-5 9:3`, `nan` / `inf` prices, `\r\n` line endings, missing files, bad JSON, usage errors.
- Read through the comments and the replaced loop in `csv_loader.py` so that I understand them.