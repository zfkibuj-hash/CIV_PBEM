"""
Email-based transport: sends save files as email attachments (SMTP)
and retrieves them from a mailbox (IMAP or POP3).

Supports two modes:
- Individual: sends save directly to the next player's email, checks own inbox.
- Shared mailbox: all players send to / check a shared mailbox.

Security options per connection:
- SSL     : immediate TLS (IMAP4_SSL / SMTP_SSL), typically port 993/465
- STARTTLS: plain connect then upgrade (IMAP4 + starttls / SMTP + starttls), port 143/587
- None    : unencrypted (not recommended)
"""
import email
import email.header
import imaplib
import logging
import poplib
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from src.transport.base import BaseTransport

logger = logging.getLogger(__name__)

SAVE_EXTENSION = ".CivBeyondSwordSave"


class EmailTransport(BaseTransport):
    """Transport via Email (SMTP for upload, IMAP/POP3 for download).

    Modes:
        - "individual": sends save to next player's email directly.
        - "shared": all players use a shared mailbox.

    Incoming protocol:
        - "imap": recommended, supports search and selective download
        - "pop3": fallback, downloads all and filters locally

    Security (per connection):
        - "SSL"      : immediate TLS (port 993/465)
        - "STARTTLS" : upgrade after connect (port 143/587)
        - "None"     : unencrypted
    """

    def __init__(self, smtp_host: str, smtp_port: int = 587,
                 smtp_user: str = "", smtp_password: str = "",
                 smtp_security: str = "STARTTLS",
                 # Legacy parameter kept for backwards compat
                 smtp_use_tls: bool = True,
                 imap_host: str = "", imap_port: int = 993,
                 imap_user: str = "", imap_password: str = "",
                 imap_security: str = "SSL",
                 # Legacy parameter kept for backwards compat
                 imap_use_ssl: bool = True,
                 incoming_protocol: str = "imap",  # "imap" or "pop3"
                 pop3_host: str = "", pop3_port: int = 995,
                 pop3_security: str = "SSL",
                 mode: str = "shared",
                 shared_email: str = "",
                 from_address: str = "",
                 delete_after_download: bool = False):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        # Support both new security param and legacy use_tls
        self.smtp_security = smtp_security if smtp_security != "STARTTLS" else (
            "STARTTLS" if smtp_use_tls else "None")

        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.imap_security = imap_security if imap_security != "SSL" else (
            "SSL" if imap_use_ssl else "STARTTLS")

        self.incoming_protocol = incoming_protocol.lower()  # "imap" or "pop3"
        self.pop3_host = pop3_host or imap_host  # fallback to imap host if not set
        self.pop3_port = pop3_port
        self.pop3_security = pop3_security

        self.mode = mode
        self.shared_email = shared_email
        self.from_address = from_address or smtp_user
        self.delete_after_download = delete_after_download
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Test incoming + SMTP connection."""
        try:
            if self.incoming_protocol == "pop3":
                pop3 = self._get_pop3()
                pop3.quit()
            else:
                imap = self._get_imap()
                imap.logout()
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Email transport connection test failed: {e}")
            self._connected = False
            return False

    def disconnect(self):
        self._connected = False

    def _get_smtp(self) -> smtplib.SMTP:
        """Create authenticated SMTP connection."""
        sec = self.smtp_security.upper()
        if sec == "SSL":
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=60)
        else:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=60)
            if sec == "STARTTLS":
                server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        return server

    def _get_imap(self) -> imaplib.IMAP4:
        """Create authenticated IMAP connection."""
        sec = self.imap_security.upper()
        if sec == "SSL":
            imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        else:
            imap = imaplib.IMAP4(self.imap_host, self.imap_port)
            if sec == "STARTTLS":
                imap.starttls()
        imap.login(self.imap_user, self.imap_password)
        return imap

    def _get_pop3(self):
        """Create authenticated POP3 connection."""
        sec = self.pop3_security.upper()
        if sec == "SSL":
            pop3 = poplib.POP3_SSL(self.pop3_host, self.pop3_port)
        else:
            pop3 = poplib.POP3(self.pop3_host, self.pop3_port)
            if sec == "STARTTLS":
                pop3.stls()
        pop3.user(self.imap_user or self.smtp_user)
        pop3.pass_(self.imap_password or self.smtp_password)
        return pop3

    def _make_subject(self, game_name: str, remote_filename: str) -> str:
        """Create a standardized subject line for game save emails."""
        return f"[CIV4PBEM] {game_name} | {remote_filename}"

    def _parse_subject(self, subject: str) -> tuple[Optional[str], Optional[str]]:
        """Parse subject line to extract game_name and filename.
        Returns (game_name, filename) or (None, None) if not a valid PBEM email."""
        if not subject or "[CIV4PBEM]" not in subject:
            return None, None
        try:
            # Format: [CIV4PBEM] GameName | filename.CivBeyondSwordSave
            parts = subject.split("[CIV4PBEM]")[1].strip()
            game_name, filename = parts.split("|", 1)
            return game_name.strip(), filename.strip()
        except (IndexError, ValueError):
            return None, None

    def _imap_search_game(self, imap, game_name: str):
        """Find message ids for one game (subject contains game name)."""
        queries = [
            f'(SUBJECT "[CIV4PBEM] {game_name} |")',
            f'(SUBJECT "[CIV4PBEM] {game_name}")',
        ]
        seen: set[bytes] = set()
        ids: list[bytes] = []
        for search_query in queries:
            status, msg_ids = imap.search(None, search_query)
            if status != "OK" or not msg_ids[0]:
                continue
            for msg_id in msg_ids[0].split():
                if msg_id not in seen:
                    seen.add(msg_id)
                    ids.append(msg_id)
        return ids

    def _message_matches_game(
        self, subject: str, game_name: str, remote_filename: str = "",
    ) -> bool:
        parsed_game, parsed_file = self._parse_subject(subject)
        if parsed_game != game_name:
            return False
        if remote_filename:
            return parsed_file == remote_filename
        return bool(parsed_file)

    def upload(self, local_path: Path, remote_filename: str, game_name: str,
               to_email: str = "") -> bool:
        """Send save file as email attachment.

        Args:
            local_path: Path to the local save file.
            remote_filename: The standardized filename for the attachment.
            game_name: Name of the game.
            to_email: Recipient email. In shared mode, uses self.shared_email.
                      In individual mode, this should be the next player's email.
        """
        recipient = to_email if (self.mode == "individual" and to_email) else self.shared_email
        if not recipient:
            logger.error("No recipient email configured for email transport")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = recipient
            msg["Subject"] = self._make_subject(game_name, remote_filename)

            body = (
                f"Civ4 PBEM save file for game: {game_name}\n"
                f"File: {remote_filename}\n\n"
                f"This message was sent automatically by Civ4 PBEM Manager.\n"
            )
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with open(local_path, "rb") as f:
                attachment = MIMEApplication(f.read(), Name=remote_filename)
            attachment["Content-Disposition"] = f'attachment; filename="{remote_filename}"'
            msg.attach(attachment)

            server = self._get_smtp()
            server.send_message(msg)
            server.quit()

            logger.info(f"Email transport: sent {remote_filename} to {recipient}")
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Email transport upload (send) failed: {e}")
            return False

    def download(self, remote_filename: str, local_path: Path, game_name: str, **kwargs) -> bool:
        """Download a specific save file from the mailbox (IMAP or POP3)."""
        if self.incoming_protocol == "pop3":
            return self._download_pop3(remote_filename, local_path, game_name)
        return self._download_imap(remote_filename, local_path, game_name)

    def _download_imap(self, remote_filename: str, local_path: Path,
                       game_name: str) -> bool:
        """Download via IMAP with optional delete after download."""
        try:
            imap = self._get_imap()
            imap.select("INBOX")

            search_query = f'(SUBJECT "[CIV4PBEM] {game_name} |")'
            status, msg_ids = imap.search(None, search_query)
            if status != "OK" or not msg_ids[0]:
                ids = self._imap_search_game(imap, game_name)
            else:
                ids = msg_ids[0].split()
            if not ids:
                imap.logout()
                return False

            for msg_id in reversed(ids):
                status, data = imap.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(data[0][1])
                subject = self._decode_header(msg.get("Subject", ""))
                parsed_game, parsed_file = self._parse_subject(subject)

                if parsed_file != remote_filename:
                    continue

                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    fname = part.get_filename()
                    if fname and fname == remote_filename:
                        with open(local_path, "wb") as f:
                            f.write(part.get_payload(decode=True))

                        if self.delete_after_download:
                            imap.store(msg_id, "+FLAGS", "\\Deleted")
                            imap.expunge()

                        imap.logout()
                        logger.info(f"Email/IMAP: downloaded {remote_filename}")
                        self._connected = True
                        return True

            imap.logout()
            return False
        except Exception as e:
            logger.error(f"Email/IMAP download failed: {e}")
            return False

    def _download_pop3(self, remote_filename: str, local_path: Path,
                       game_name: str) -> bool:
        """Download via POP3 — fetches all messages and filters locally."""
        try:
            pop3 = self._get_pop3()
            num_messages = len(pop3.list()[1])

            for i in range(num_messages, 0, -1):  # newest first
                lines = pop3.retr(i)[1]
                raw = b"\r\n".join(lines)
                msg = email.message_from_bytes(raw)
                subject = self._decode_header(msg.get("Subject", ""))
                parsed_game, parsed_file = self._parse_subject(subject)

                if parsed_game != game_name or parsed_file != remote_filename:
                    continue

                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    fname = part.get_filename()
                    if fname and fname == remote_filename:
                        with open(local_path, "wb") as f:
                            f.write(part.get_payload(decode=True))

                        if self.delete_after_download:
                            pop3.dele(i)

                        pop3.quit()
                        logger.info(f"Email/POP3: downloaded {remote_filename}")
                        self._connected = True
                        return True

            pop3.quit()
            return False
        except Exception as e:
            logger.error(f"Email/POP3 download failed: {e}")
            return False

    def list_files(self, game_name: str) -> list[str]:
        """List all save file attachments available for a game in the mailbox."""
        if self.incoming_protocol == "pop3":
            return self._list_files_pop3(game_name)
        return self._list_files_imap(game_name)

    def _list_files_imap(self, game_name: str) -> list[str]:
        try:
            imap = self._get_imap()
            imap.select("INBOX")

            ids = self._imap_search_game(imap, game_name)
            if not ids:
                imap.logout()
                return []

            files = []
            for msg_id in ids:
                status, data = imap.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                msg = email.message_from_bytes(data[0][1])
                subject = self._decode_header(msg.get("Subject", ""))
                parsed_game, parsed_file = self._parse_subject(subject)
                if parsed_game == game_name and parsed_file:
                    files.append(parsed_file)

            imap.logout()
            self._connected = True
            return files
        except Exception as e:
            logger.error(f"Email/IMAP list_files failed: {e}")
            return []

    def _list_files_pop3(self, game_name: str) -> list[str]:
        try:
            pop3 = self._get_pop3()
            num_messages = len(pop3.list()[1])
            files = []
            for i in range(1, num_messages + 1):
                # Fetch only headers to save bandwidth
                lines = pop3.top(i, 0)[1]
                raw = b"\r\n".join(lines)
                msg = email.message_from_bytes(raw)
                subject = self._decode_header(msg.get("Subject", ""))
                parsed_game, parsed_file = self._parse_subject(subject)
                if parsed_game == game_name and parsed_file:
                    files.append(parsed_file)
            pop3.quit()
            self._connected = True
            return files
        except Exception as e:
            logger.error(f"Email/POP3 list_files failed: {e}")
            return []

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        files = self.list_files(game_name)
        return remote_filename in files

    def delete(self, remote_filename: str, game_name: str) -> bool:
        """Delete the mailbox message that carries this save attachment."""
        if self.incoming_protocol == "pop3":
            return self._delete_pop3(remote_filename, game_name)
        return self._delete_imap(remote_filename, game_name)

    def _delete_imap(self, remote_filename: str, game_name: str) -> bool:
        try:
            imap = self._get_imap()
            imap.select("INBOX")
            ids = self._imap_search_game(imap, game_name)
            if not ids:
                imap.logout()
                return False
            for msg_id in ids:
                status, data = imap.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                msg = email.message_from_bytes(data[0][1])
                subject = self._decode_header(msg.get("Subject", ""))
                _parsed_game, parsed_file = self._parse_subject(subject)
                if parsed_file == remote_filename:
                    imap.store(msg_id, "+FLAGS", "\\Deleted")
                    imap.expunge()
                    imap.logout()
                    logger.info("Email/IMAP: deleted %s", remote_filename)
                    self._connected = True
                    return True
            imap.logout()
            return False
        except Exception as e:
            logger.error("Email/IMAP delete failed: %s", e)
            return False

    def _delete_pop3(self, remote_filename: str, game_name: str) -> bool:
        try:
            pop3 = self._get_pop3()
            num_messages = len(pop3.list()[1])
            for i in range(num_messages, 0, -1):
                lines = pop3.top(i, 0)[1]
                msg = email.message_from_bytes(b"\r\n".join(lines))
                subject = self._decode_header(msg.get("Subject", ""))
                parsed_game, parsed_file = self._parse_subject(subject)
                if parsed_game == game_name and parsed_file == remote_filename:
                    pop3.dele(i)
                    pop3.quit()
                    logger.info("Email/POP3: deleted %s", remote_filename)
                    self._connected = True
                    return True
            pop3.quit()
            return False
        except Exception as e:
            logger.error("Email/POP3 delete failed: %s", e)
            return False

    def _decode_header(self, header_value: str) -> str:
        """Decode a potentially encoded email header."""
        if not header_value:
            return ""
        decoded_parts = email.header.decode_header(header_value)
        result = ""
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(charset or "utf-8", errors="replace")
            else:
                result += part
        return result


    def purge_game(self, game_name: str) -> tuple[bool, int]:
        """Delete ALL emails associated with a specific game from the mailbox."""
        if self.incoming_protocol == "pop3":
            return self._purge_game_pop3(game_name)
        return self._purge_game_imap(game_name)

    def _purge_game_imap(self, game_name: str) -> tuple[bool, int]:
        try:
            imap = self._get_imap()
            imap.select("INBOX")
            ids = self._imap_search_game(imap, game_name)
            if not ids:
                imap.logout()
                return True, 0

            for msg_id in ids:
                imap.store(msg_id, "+FLAGS", "\\Deleted")

            imap.expunge()
            imap.logout()
            logger.info("Purged %s emails for game '%s'", len(ids), game_name)
            return True, len(ids)
        except Exception as e:
            logger.error(f"Failed to purge emails for game '{game_name}': {e}")
            return False, 0

    def _purge_game_pop3(self, game_name: str) -> tuple[bool, int]:
        try:
            pop3 = self._get_pop3()
            num_messages = len(pop3.list()[1])
            count = 0
            for i in range(num_messages, 0, -1):
                lines = pop3.top(i, 0)[1]
                msg = email.message_from_bytes(b"\r\n".join(lines))
                subject = self._decode_header(msg.get("Subject", ""))
                if self._message_matches_game(subject, game_name):
                    pop3.dele(i)
                    count += 1
            pop3.quit()
            logger.info("Purged %s POP3 emails for game '%s'", count, game_name)
            return True, count
        except Exception as e:
            logger.error(f"Failed to purge POP3 emails for game '{game_name}': {e}")
            return False, 0
