import logging

audit_logger = logging.getLogger("audit")


def audit(event: str, **details: object) -> None:
    parts = [f"{key}={value}" for key, value in details.items()]
    suffix = " ".join(parts)
    audit_logger.info("%s%s", event, f" {suffix}" if suffix else "")
