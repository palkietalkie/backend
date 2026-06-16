import ipaddress


def is_blocked_host(host: str) -> bool:
    """Basic SSRF guard: refuse localhost and private / loopback / link-local / reserved IPs.

    The backend holds DB + KG credentials, so a fetch tool must never be steerable at internal hosts.
    """
    if host.lower() in {"localhost", ""}:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
