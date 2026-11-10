#!/usr/bin/env python3

import json
import sys
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Expected the Wazuh alert file and Alertmanager URL.")

    with open(sys.argv[1], encoding="utf-8") as alert_file:
        event = json.load(alert_file)

    rule = event.get("rule", {})
    agent = event.get("agent", {})
    level = int(rule.get("level", 0))
    rule_id = str(rule.get("id", "unknown"))
    agent_name = agent.get("name") or "wazuh-manager"
    description = str(rule.get("description") or "Wazuh security alert")
    severity = "critical" if level >= 12 else "warning"

    now = datetime.now(timezone.utc)
    alert = {
        "labels": {
            "alertname": "WazuhSecurityAlert",
            "severity": severity,
            "instance": agent_name,
            "job": "wazuh",
            "wazuh_rule_id": rule_id,
        },
        "annotations": {
            "summary": f"Wazuh level {level}: {description}",
            "description": (
                f"Agent: {agent_name}; rule: {rule_id}; "
                f"location: {event.get('location', 'unknown')}"
            ),
        },
        "startsAt": now.isoformat(),
        "endsAt": (now + timedelta(minutes=5)).isoformat(),
    }

    request = Request(
        sys.argv[2],
        data=json.dumps([alert]).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Alertmanager returned HTTP {response.status}")


if __name__ == "__main__":
    main()
