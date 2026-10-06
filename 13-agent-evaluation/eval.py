import re
from datetime import datetime

from app import SYSTEM_PROMPT, run_agent


WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

TRIALS = 5


def extract_final_weekday(response):
    pattern = r"\b(" + "|".join(WEEKDAYS) + r")\b"

    matches = re.findall(
        pattern,
        response,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    return matches[-1].capitalize()


def extract_temperature(response):
    match = re.search(
        r"(-?\d+(?:\.\d+)?)\s*°?\s*C\b",
        response,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return float(match.group(1))


def evaluate_current_weekday():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What day of the week is it?",
        },
    ]

    result = run_agent(messages)

    response = result["response"]
    tool_events = result["tool_events"]

    date_time_events = [
        event
        for event in tool_events
        if event["tool"] == "get_current_date_time"
    ]

    tool_selection_pass = len(date_time_events) > 0

    tool_execution_pass = (
        tool_selection_pass
        and date_time_events[-1]["success"]
    )

    expected_weekday = None

    if tool_execution_pass:
        observed_datetime = date_time_events[-1]["result"]["datetime"]

        expected_weekday = datetime.fromisoformat(
            observed_datetime
        ).strftime("%A")

    actual_weekday = extract_final_weekday(response)

    answer_correctness_pass = (
        expected_weekday is not None
        and actual_weekday is not None
        and actual_weekday == expected_weekday
    )

    overall_pass = (
        tool_selection_pass
        and tool_execution_pass
        and answer_correctness_pass
    )

    return {
        "tool_selection": tool_selection_pass,
        "tool_execution": tool_execution_pass,
        "answer_correctness": answer_correctness_pass,
        "overall": overall_pass,
        "expected_weekday": expected_weekday,
        "actual_weekday": actual_weekday,
        "response": response,
        "trace_id": result["trace_id"],
    }


def evaluate_cpu_temperature():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What is the current CPU temperature?",
        },
    ]

    result = run_agent(messages)

    response = result["response"]
    tool_events = result["tool_events"]

    temperature_events = [
        event
        for event in tool_events
        if event["tool"] == "get_cpu_temperature"
    ]

    tool_selection_pass = len(temperature_events) > 0

    tool_execution_pass = (
        tool_selection_pass
        and temperature_events[-1]["success"]
    )

    expected_temperature = None

    if tool_execution_pass:
        expected_temperature = temperature_events[-1]["result"][
            "temperature_celsius"
        ]

    actual_temperature = extract_temperature(response)

    answer_correctness_pass = (
        expected_temperature is not None
        and actual_temperature is not None
        and actual_temperature == expected_temperature
    )

    overall_pass = (
        tool_selection_pass
        and tool_execution_pass
        and answer_correctness_pass
    )

    return {
        "tool_selection": tool_selection_pass,
        "tool_execution": tool_execution_pass,
        "answer_correctness": answer_correctness_pass,
        "overall": overall_pass,
        "expected_temperature": expected_temperature,
        "actual_temperature": actual_temperature,
        "response": response,
        "trace_id": result["trace_id"],
    }


def evaluate_system_info():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What system are you running on?",
        },
    ]

    result = run_agent(messages)

    response = result["response"]
    tool_events = result["tool_events"]

    system_info_events = [
        event
        for event in tool_events
        if event["tool"] == "get_system_info"
    ]

    tool_selection_pass = len(system_info_events) > 0

    tool_execution_pass = (
        tool_selection_pass
        and system_info_events[-1]["success"]
    )

    expected_system_info = None
    matched_fields = []

    if tool_execution_pass:
        expected_system_info = system_info_events[-1]["result"]

        response_lower = response.lower()

        for field, value in expected_system_info.items():
            if str(value).lower() in response_lower:
                matched_fields.append(field)

    answer_correctness_pass = (
        expected_system_info is not None
        and len(matched_fields) == len(expected_system_info)
    )

    overall_pass = (
        tool_selection_pass
        and tool_execution_pass
        and answer_correctness_pass
    )

    return {
        "tool_selection": tool_selection_pass,
        "tool_execution": tool_execution_pass,
        "answer_correctness": answer_correctness_pass,
        "overall": overall_pass,
        "expected_system_info": expected_system_info,
        "matched_fields": matched_fields,
        "expected": list(expected_system_info.keys()) if expected_system_info else [],
        "actual": matched_fields,
        "response": response,
        "trace_id": result["trace_id"],
    }


def evaluate_no_tool():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        },
    ]

    result = run_agent(messages)

    response = result["response"]
    tool_events = result["tool_events"]

    tool_selection_pass = len(tool_events) == 0

    tool_execution_pass = tool_selection_pass

    expected_answer = "Paris"

    answer_correctness_pass = (
        expected_answer.lower() in response.lower()
    )

    overall_pass = (
        tool_selection_pass
        and tool_execution_pass
        and answer_correctness_pass
    )

    return {
        "tool_selection": tool_selection_pass,
        "tool_execution": tool_execution_pass,
        "answer_correctness": answer_correctness_pass,
        "overall": overall_pass,
        "expected_answer": expected_answer,
        "actual_answer": response,
        "response": response,
        "trace_id": result["trace_id"],
    }


def percentage(passed, total):
    return (passed / total) * 100


EVALUATION_CASES = [
    {
        "name": "current_weekday",
        "evaluator": evaluate_current_weekday,
        "expected_key": "expected_weekday",
        "actual_key": "actual_weekday",
    },
    {
        "name": "cpu_temperature",
        "evaluator": evaluate_cpu_temperature,
        "expected_key": "expected_temperature",
        "actual_key": "actual_temperature",
    },
    {
        "name": "system_info",
        "evaluator": evaluate_system_info,
        "expected_key": "expected",
        "actual_key": "actual",
    },
    {
        "name": "no_tool",
        "evaluator": evaluate_no_tool,
        "expected_key": "expected_answer",
        "actual_key": "actual_answer",
    },
]


def run_case(case):
    results = []

    print("\n===== EVALUATION =====")
    print(f"CASE: {case['name']}")
    print(f"TRIALS: {TRIALS}")
    print()

    for trial in range(1, TRIALS + 1):
        result = case["evaluator"]()
        results.append(result)

        status = "PASS" if result["overall"] else "FAIL"

        expected = result[case["expected_key"]]
        actual = result[case["actual_key"]]

        print(
            f"Trial {trial}: {status} "
            f"(expected={expected}, actual={actual})"
        )

    tool_selection_passes = sum(
        result["tool_selection"] for result in results
    )

    tool_execution_passes = sum(
        result["tool_execution"] for result in results
    )

    answer_correctness_passes = sum(
        result["answer_correctness"] for result in results
    )

    overall_passes = sum(
        result["overall"] for result in results
    )

    summary = {
        "name": case["name"],
        "trials": TRIALS,
        "tool_selection": tool_selection_passes,
        "tool_execution": tool_execution_passes,
        "answer_correctness": answer_correctness_passes,
        "overall": overall_passes,
    }

    print("\n----- CASE SUMMARY -----")
    print(f"Case: {case['name']}")
    print(f"Trials: {TRIALS}")
    print()

    print(
        f"Tool selection:       "
        f"{tool_selection_passes}/{TRIALS}  "
        f"{percentage(tool_selection_passes, TRIALS):.1f}%"
    )

    print(
        f"Tool execution:       "
        f"{tool_execution_passes}/{TRIALS}  "
        f"{percentage(tool_execution_passes, TRIALS):.1f}%"
    )

    print(
        f"Answer correctness:   "
        f"{answer_correctness_passes}/{TRIALS}  "
        f"{percentage(answer_correctness_passes, TRIALS):.1f}%"
    )

    print(
        f"Overall passes:       "
        f"{overall_passes}/{TRIALS}  "
        f"{percentage(overall_passes, TRIALS):.1f}%"
    )

    return summary


def main():
    summaries = []

    for case in EVALUATION_CASES:
        summary = run_case(case)
        summaries.append(summary)

    print("\n===== OVERALL SUMMARY =====")
    print()

    for summary in summaries:
        trials = summary["trials"]

        print(
            f"{summary['name']}: "
            f"{summary['overall']}/{trials}  "
            f"{percentage(summary['overall'], trials):.1f}%"
        )


if __name__ == "__main__":
    main()
