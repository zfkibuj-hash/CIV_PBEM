"""
Email server autodiscovery for Civ4 PBEM Manager.

Tries multiple methods in order:
1. Known presets (Gmail, Outlook, Yahoo, iCloud)
2. Mozilla Thunderbird autoconfig XML
3. Microsoft Autodiscover XML
4. DNS SRV records (RFC 6186)
5. Common hostname guesses (imap.domain, mail.domain, etc.)

Returns EmailServerConfig with IMAP and SMTP settings.
All results are suggestions — user can always override manually.
"""
import logging
import socket
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for one mail server (IMAP or SMTP)."""
    host: str
    port: int
    security: str  # "SSL", "STARTTLS", "None"

    def __str__(self):
        return f"{self.host}:{self.port} ({self.security})"


@dataclass
class EmailServerConfig:
    """Complete discovered email server configuration."""
    imap: Optional[ServerConfig] = None
    smtp: Optional[ServerConfig] = None
    source: str = ""  # How it was discovered (for UI display)

    @property
    def is_complete(self) -> bool:
        return self.imap is not None and self.smtp is not None


# --- Known presets for major providers ---
_PRESETS: dict[str, EmailServerConfig] = {
    "gmail.com": EmailServerConfig(
        imap=ServerConfig("imap.gmail.com", 993, "SSL"),
        smtp=ServerConfig("smtp.gmail.com", 587, "STARTTLS"),
        source="preset",
    ),
    "googlemail.com": EmailServerConfig(
        imap=ServerConfig("imap.gmail.com", 993, "SSL"),
        smtp=ServerConfig("smtp.gmail.com", 587, "STARTTLS"),
        source="preset",
    ),
    "outlook.com": EmailServerConfig(
        imap=ServerConfig("imap-mail.outlook.com", 993, "SSL"),
        smtp=ServerConfig("smtp-mail.outlook.com", 587, "STARTTLS"),
        source="preset",
    ),
    "hotmail.com": EmailServerConfig(
        imap=ServerConfig("imap-mail.outlook.com", 993, "SSL"),
        smtp=ServerConfig("smtp-mail.outlook.com", 587, "STARTTLS"),
        source="preset",
    ),
    "live.com": EmailServerConfig(
        imap=ServerConfig("imap-mail.outlook.com", 993, "SSL"),
        smtp=ServerConfig("smtp-mail.outlook.com", 587, "STARTTLS"),
        source="preset",
    ),
    "msn.com": EmailServerConfig(
        imap=ServerConfig("imap-mail.outlook.com", 993, "SSL"),
        smtp=ServerConfig("smtp-mail.outlook.com", 587, "STARTTLS"),
        source="preset",
    ),
    "yahoo.com": EmailServerConfig(
        imap=ServerConfig("imap.mail.yahoo.com", 993, "SSL"),
        smtp=ServerConfig("smtp.mail.yahoo.com", 587, "STARTTLS"),
        source="preset",
    ),
    "yahoo.co.uk": EmailServerConfig(
        imap=ServerConfig("imap.mail.yahoo.com", 993, "SSL"),
        smtp=ServerConfig("smtp.mail.yahoo.com", 587, "STARTTLS"),
        source="preset",
    ),
    "icloud.com": EmailServerConfig(
        imap=ServerConfig("imap.mail.me.com", 993, "SSL"),
        smtp=ServerConfig("smtp.mail.me.com", 587, "STARTTLS"),
        source="preset",
    ),
    "me.com": EmailServerConfig(
        imap=ServerConfig("imap.mail.me.com", 993, "SSL"),
        smtp=ServerConfig("smtp.mail.me.com", 587, "STARTTLS"),
        source="preset",
    ),
    "mac.com": EmailServerConfig(
        imap=ServerConfig("imap.mail.me.com", 993, "SSL"),
        smtp=ServerConfig("smtp.mail.me.com", 587, "STARTTLS"),
        source="preset",
    ),
}


def discover(email_address: str, timeout: int = 5) -> Optional[EmailServerConfig]:
    """Attempt to auto-discover mail server settings for an email address.

    Tries in order:
    1. Known presets
    2. Mozilla autoconfig
    3. Microsoft Autodiscover
    4. DNS SRV records
    5. Common hostname guesses

    Args:
        email_address: Full email address (user@domain.com)
        timeout: HTTP/DNS timeout in seconds

    Returns:
        EmailServerConfig if discovered, None if all methods failed.
    """
    if "@" not in email_address:
        return None

    domain = email_address.split("@", 1)[1].lower().strip()
    logger.info(f"Autodiscover: trying domain '{domain}'")

    # 1. Known presets (instant, no network)
    result = _try_presets(domain)
    if result:
        logger.info(f"Autodiscover: found preset for {domain}")
        return result

    # 2. Mozilla autoconfig XML
    result = _try_mozilla_autoconfig(domain, email_address, timeout)
    if result and result.is_complete:
        logger.info(f"Autodiscover: Mozilla autoconfig succeeded for {domain}")
        return result

    # 3. Microsoft Autodiscover
    result = _try_ms_autodiscover(domain, email_address, timeout)
    if result and result.is_complete:
        logger.info(f"Autodiscover: MS Autodiscover succeeded for {domain}")
        return result

    # 4. DNS SRV records
    result = _try_dns_srv(domain, timeout)
    if result and result.is_complete:
        logger.info(f"Autodiscover: DNS SRV succeeded for {domain}")
        return result

    # 5. Common hostname guesses
    result = _try_common_hosts(domain, timeout)
    if result and result.is_complete:
        logger.info(f"Autodiscover: common host guess succeeded for {domain}")
        return result

    logger.warning(f"Autodiscover: all methods failed for {domain}")
    return None


def _try_presets(domain: str) -> Optional[EmailServerConfig]:
    return _PRESETS.get(domain)


def _try_mozilla_autoconfig(domain: str, email: str, timeout: int) -> Optional[EmailServerConfig]:
    """Try Mozilla Thunderbird autoconfig standard (XML)."""
    try:
        import requests as req
        urls = [
            f"https://autoconfig.{domain}/mail/config-v1.1.xml",
            f"https://{domain}/.well-known/autoconfig/mail/config-v1.1.xml",
            f"http://autoconfig.{domain}/mail/config-v1.1.xml",
            # Mozilla ISPDB fallback
            f"https://autoconfig.thunderbird.net/v1.1/{domain}",
        ]
        for url in urls:
            try:
                r = req.get(url, timeout=timeout, params={"emailaddress": email})
                if r.status_code == 200 and "clientConfig" in r.text:
                    return _parse_mozilla_xml(r.text)
            except Exception:
                continue
    except ImportError:
        logger.warning("requests not available, skipping Mozilla autoconfig")
    return None


def _parse_mozilla_xml(xml_text: str) -> Optional[EmailServerConfig]:
    """Parse Mozilla autoconfig XML into EmailServerConfig."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_text)
        imap_cfg = None
        smtp_cfg = None

        for server in root.iter("incomingServer"):
            stype = server.get("type", "").lower()
            if stype == "imap" and imap_cfg is None:
                host = _xml_text(server, "hostname")
                port = int(_xml_text(server, "port", "993"))
                sec = _map_mozilla_security(_xml_text(server, "socketType"))
                if host:
                    imap_cfg = ServerConfig(host, port, sec)

        for server in root.iter("outgoingServer"):
            stype = server.get("type", "").lower()
            if stype == "smtp" and smtp_cfg is None:
                host = _xml_text(server, "hostname")
                port = int(_xml_text(server, "port", "587"))
                sec = _map_mozilla_security(_xml_text(server, "socketType"))
                if host:
                    smtp_cfg = ServerConfig(host, port, sec)

        if imap_cfg or smtp_cfg:
            return EmailServerConfig(imap=imap_cfg, smtp=smtp_cfg, source="Mozilla autoconfig")
    except Exception as e:
        logger.debug(f"Mozilla XML parse error: {e}")
    return None


def _xml_text(element, tag: str, default: str = "") -> str:
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else default


def _map_mozilla_security(socket_type: str) -> str:
    s = socket_type.upper()
    if "SSL" in s:
        return "SSL"
    if "STARTTLS" in s or "TLS" in s:
        return "STARTTLS"
    return "None"


def _try_ms_autodiscover(domain: str, email: str, timeout: int) -> Optional[EmailServerConfig]:
    """Try Microsoft Autodiscover (Outlook/Exchange standard)."""
    try:
        import requests as req
        urls = [
            f"https://autodiscover.{domain}/autodiscover/autodiscover.xml",
            f"https://{domain}/autodiscover/autodiscover.xml",
        ]
        headers = {"Content-Type": "text/xml"}
        body = f"""<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/requestschema/2006">
  <Request>
    <EMailAddress>{email}</EMailAddress>
    <AcceptableResponseSchema>http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a</AcceptableResponseSchema>
  </Request>
</Autodiscover>"""
        for url in urls:
            try:
                r = req.post(url, data=body, headers=headers, timeout=timeout)
                if r.status_code == 200:
                    return _parse_ms_autodiscover_xml(r.text)
            except Exception:
                continue
    except ImportError:
        pass
    return None


def _parse_ms_autodiscover_xml(xml_text: str) -> Optional[EmailServerConfig]:
    """Parse Microsoft Autodiscover XML."""
    try:
        import xml.etree.ElementTree as ET
        # Strip namespaces for easier parsing
        import re
        xml_text = re.sub(r'\sxmlns[^"]*"[^"]*"', '', xml_text)
        root = ET.fromstring(xml_text)

        imap_cfg = None
        smtp_cfg = None

        for protocol in root.iter("Protocol"):
            ptype = _xml_text(protocol, "Type", "").upper()
            host = _xml_text(protocol, "Server")
            port_str = _xml_text(protocol, "Port")
            ssl = _xml_text(protocol, "SSL", "On").upper()
            enc = _xml_text(protocol, "Encryption", "").upper()

            if not host or not port_str:
                continue
            port = int(port_str)

            # Determine security
            if ssl == "ON" or enc == "SSL":
                sec = "SSL"
            elif enc in ("TLS", "STARTTLS"):
                sec = "STARTTLS"
            else:
                sec = "None"

            if ptype == "IMAP" and imap_cfg is None:
                imap_cfg = ServerConfig(host, port, sec)
            elif ptype == "SMTP" and smtp_cfg is None:
                smtp_cfg = ServerConfig(host, port, sec)

        if imap_cfg or smtp_cfg:
            return EmailServerConfig(imap=imap_cfg, smtp=smtp_cfg,
                                     source="MS Autodiscover")
    except Exception as e:
        logger.debug(f"MS Autodiscover XML parse error: {e}")
    return None


def _try_dns_srv(domain: str, timeout: int) -> Optional[EmailServerConfig]:
    """Try DNS SRV records (RFC 6186)."""
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout

        imap_cfg = None
        smtp_cfg = None

        # IMAP SRV records
        for srv_name, port_default, sec in [
            (f"_imaps._tcp.{domain}", 993, "SSL"),
            (f"_imap._tcp.{domain}", 143, "STARTTLS"),
        ]:
            if imap_cfg:
                break
            try:
                answers = resolver.resolve(srv_name, "SRV")
                for rdata in answers:
                    host = str(rdata.target).rstrip(".")
                    port = int(rdata.port) or port_default
                    imap_cfg = ServerConfig(host, port, sec)
                    break
            except Exception:
                continue

        # SMTP SRV records
        for srv_name, port_default, sec in [
            (f"_submissions._tcp.{domain}", 465, "SSL"),
            (f"_submission._tcp.{domain}", 587, "STARTTLS"),
        ]:
            if smtp_cfg:
                break
            try:
                answers = resolver.resolve(srv_name, "SRV")
                for rdata in answers:
                    host = str(rdata.target).rstrip(".")
                    port = int(rdata.port) or port_default
                    smtp_cfg = ServerConfig(host, port, sec)
                    break
            except Exception:
                continue

        if imap_cfg or smtp_cfg:
            return EmailServerConfig(imap=imap_cfg, smtp=smtp_cfg,
                                     source="DNS SRV")
    except ImportError:
        logger.warning("dnspython not available, skipping DNS SRV")
    except Exception as e:
        logger.debug(f"DNS SRV error: {e}")
    return None


def _try_common_hosts(domain: str, timeout: int) -> Optional[EmailServerConfig]:
    """Try common hostname patterns and verify by TCP connect."""
    imap_candidates = [
        (f"imap.{domain}", 993, "SSL"),
        (f"mail.{domain}", 993, "SSL"),
        (f"imap.{domain}", 143, "STARTTLS"),
        (f"mail.{domain}", 143, "STARTTLS"),
    ]
    smtp_candidates = [
        (f"smtp.{domain}", 587, "STARTTLS"),
        (f"mail.{domain}", 587, "STARTTLS"),
        (f"smtp.{domain}", 465, "SSL"),
        (f"mail.{domain}", 465, "SSL"),
    ]

    imap_cfg = _first_reachable(imap_candidates, timeout)
    smtp_cfg = _first_reachable(smtp_candidates, timeout)

    if imap_cfg or smtp_cfg:
        return EmailServerConfig(imap=imap_cfg, smtp=smtp_cfg,
                                 source="common host guess")
    return None


def _first_reachable(candidates: list, timeout: int) -> Optional[ServerConfig]:
    """Return first (host, port, security) tuple that accepts a TCP connection."""
    for host, port, sec in candidates:
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return ServerConfig(host, port, sec)
        except (socket.timeout, socket.error, OSError):
            continue
    return None
