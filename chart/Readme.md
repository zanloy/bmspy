# Helm Chart: bmspy
---

This chart will install a deployment with replicas=1 that is designed to do two things:

* Listen to requests from Slack and return results from health check
* Monitor bms-api websocket and alert `channel` on health changes

# Parameters
---

| Name | Description | Value |
| --- | --- | --- |
| `args` | The arguments to pass into bmspy.py. | `["--source=https://bms-api.bms:8080", "--log-level=INFO"]` |
| `image` | The docker image to deploy. | `NO DEFAULT, REQUIRED` |
| `namespace` | The namespace to deploy to. | `"bms"` |