"""Conservative public-website URL checks. Also enforce network egress isolation in production."""
import ipaddress
import socket
from urllib.parse import urlsplit


class UnsafeTarget(ValueError):
    pass


def validate_public_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise UnsafeTarget("A short HTTP(S) URL is required")
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").rstrip(".").lower()
        port = parsed.port
    except ValueError as exc:
        raise UnsafeTarget("Malformed target URL") from exc
    if parsed.scheme not in ("https", "http") or not host:
        raise UnsafeTarget("Only HTTP(S) hostnames are allowed")
    if parsed.username or parsed.password or parsed.fragment:
        raise UnsafeTarget("Credentials and fragments are not allowed")
    if port is not None and port not in (80, 443):
        raise UnsafeTarget("Only ports 80 and 443 are permitted")
    if host in ("localhost",) or host.endswith((".localhost", ".local", ".internal", ".test", ".onion")):
        raise UnsafeTarget("Internal hostnames are not permitted")
    try:
        literal = ipaddress.ip_address(host)
        if not literal.is_global:
            raise UnsafeTarget("Private or special-use IPs are not permitted")
    except ValueError:
        if not all(label and len(label) <= 63 for label in host.split(".")):
            raise UnsafeTarget("Malformed hostname")
        if "." not in host:
            raise UnsafeTarget("A public hostname is required")
    try:
        infos = socket.getaddrinfo(host, port or (443 if parsed.scheme == "https" else 80),
                                   type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeTarget("Hostname could not be resolved") from exc
    addresses = {i[4][0] for i in infos}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise UnsafeTarget("Destination resolved to a non-public IP")
    return url


def validate_syntactic_url(url: str) -> str:
    """Check syntax without DNS; browser worker performs full URL check before each request."""
    try:
        p = urlsplit(url)
        if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
            raise ValueError
        if p.port is not None and p.port not in (80, 443):
            raise ValueError
    except ValueError as exc:
        raise UnsafeTarget("Invalid or restricted URL") from exc
    return url
