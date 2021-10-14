from typing import Any, List

ALERT_PREFIX=':question:'
ERROR_PREFIX=':small_red_triangle:'
WARNING_PREFIX=':small_orange_diamond:'

def get_or_die(subj: dict, key: str) -> Any:
    if key not in subj.keys():
        raise KeyError(f'{key} is missing')
    return subj[key]

def lines_markdown(items: List[str], prefix: str=''):
    lines: List[str] = []
    for item in items:
        lines.append(f'{prefix} {item}')
    return "\n".join(lines)

def alerts_markdown(alerts: List[str]):
    return lines_markdown(alerts, prefix=ALERT_PREFIX)

def errors_markdown(errors: List[str]):
    return lines_markdown(errors, prefix=ERROR_PREFIX)

def warnings_markdown(warnings: List[str]):
    return lines_markdown(warnings, prefix=WARNING_PREFIX)