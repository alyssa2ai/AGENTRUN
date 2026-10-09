# Benchmark

The benchmark has 23 tasks, defined in [`eval/tasks.py`](../eval/tasks.py) and scored by `score_task()` in [`eval/harness.py`](../eval/harness.py). Both files are **frozen**: changing either one breaks comparability with the committed Base, V1, E4, and V2 results.

## Scoring rules

A task passes only if **all** of the following hold:

1. Every tool in `required_tools` was called at least once. Extra or unnecessary tool calls are **not** penalized.
2. No tool call produced an error. For the one task with `expect_tool_error=True`, it is the other way round: at least one tool error is required.
3. The run did not reach the `max_steps=3` budget.
4. The final answer contains every `answer_contains` string and at least one `answer_contains_any` string. Both checks are case-insensitive substring matches.
5. If `numeric_check=(value, tol)` is set, some number in the final answer is within `tol` of `value`. Commas are ignored.

## Tasks and predicates

| Task | Category | Required tools | Content predicate |
|---|---|---|---|
| `calc_basic_1` | math | calculator | number 6016 ± 0.5 |
| `calc_basic_2` | math | calculator | number 75 ± 0.5 |
| `calc_order_of_ops` | math | calculator | number 50 ± 0.5 |
| `wordcount_basic` | text | word_count | number 9 ± 0.5 |
| `weather_basic_1` | weather | get_weather | none |
| `weather_basic_2` | weather | get_weather | none |
| `search_basic_1` | search | web_search | none |
| `search_basic_2` | search | web_search | contains `canberra` |
| `multi_weather_calc` | multi_tool | calculator, get_weather | number 540 ± 0.5 |
| `multi_wordcount_calc` | multi_tool | calculator, word_count | number 700 ± 0.5 |
| `multi_search_weather` | multi_tool | get_weather, web_search | none |
| `multi_three_tools` | multi_tool | calculator, get_weather, web_search | number 305989 ± 0.5 |
| `chain_weather_then_calc` | chained_reasoning | calculator, get_weather | none |
| `time_sensitive_1` | time_sensitive | web_search | none |
| `no_tool_needed_1` | no_tool_expected | none | contains `au` |
| `no_tool_needed_2` | no_tool_expected | none | none |
| `adversarial_negative_multiply` | adversarial_math | calculator | number −612 ± 0.5 |
| `adversarial_decimal_division` | adversarial_math | calculator | number 2.125 ± 0.01 |
| `adversarial_percentage` | adversarial_math | calculator | number 51 ± 0.5 |
| `adversarial_false_premise` | adversarial_reasoning | web_search | any of `fictional`, `doesn't exist`, `does not exist`, `not a real country`, `not real`, `marvel` |
| `adversarial_chained_search_calc` | adversarial_reasoning | calculator, web_search | number 19 ± 1 |
| `adversarial_division_by_zero` | adversarial_error_handling | calculator | **tool error required**; any of `undefined`, `cannot divide`, `not defined`, `infinite`, `error`, `division by zero` |
| `adversarial_ambiguous_city` | adversarial_ambiguity | get_weather | none |

## How strong each predicate is

`tests/test_benchmark_and_data.py::test_predicate_strength_is_as_documented` pins these counts:

- **15 tasks** check answer content as well as tool use.
- **7 tasks** check only that the required tools were called without error: `weather_basic_1`, `weather_basic_2`, `search_basic_1`, `multi_search_weather`, `chain_weather_then_calc`, `time_sensitive_1`, and `adversarial_ambiguous_city`. Their correct answers depend on live data and cannot be fixed in advance. For `chain_weather_then_calc`, the Fahrenheit value itself is **not** checked.
- **1 task** (`no_tool_needed_2`) has no positive check. Any answer passes unless a tool errors or the step budget is exhausted.
- Some content checks are weak. `no_tool_needed_1` passes on any answer containing the substring `au`. `adversarial_chained_search_calc` assumes the year 2026.

As a result, a pass on a tool-only task means the agent *called the right tools*, not that the answer it gave was correct. For example, in V1 `multi_search_weather` passed with a final answer that named the wrong UK Prime Minister, even though the search result it had just received gave the correct name.

## Train/benchmark separation

- **Prompt level:** none of the 35 V1 or 46 V2 training prompts equals a benchmark prompt after case and whitespace normalization (tested).
- **Template and category level:** not separated. The 11 V2 additions were written after V1 failures on these tasks and follow the same templates. Examples: word-count-then-multiply, weather-then-Celsius-to-Fahrenheit, three-tool queries, `X divided by 0`, and a fictional-country false premise.
- **Generalization:** not tested. No held-out benchmark constructed independently of V1's failures exists yet. This is planned as E8 and has not been run.
