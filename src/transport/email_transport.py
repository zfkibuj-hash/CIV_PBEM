"""
Email-based transport: sends save files as email attachments (SMTP)
and retrieves them from a mailbox (IMAP).

Supports two modes:
- Individual: sends save directly to the next player's email, checks own inbox.
- Shared mailbox: all players send to / check a shared mailbox (e.g. civ4pbem@...).
  In shared mode, saves are identified by subject line containing game name and turn info.

Naming convention for attachments:
    {game_name}_T{turn_number:04d}_{sender_name}.CivBeyondSwordSave

The sender_name is the player who FINISHED their turn and is uploading.
This way the recipient knows who sent it, and it's easy to sort chronologically.
"""
import email
import email.header
import imaplib
import logging
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
    """Transport via Email (SMTP for upload, IMAP for download).

    Modes:
        - "individual": sends save to next player's email directly.
          Each player checks their own inbox for saves.
        - "shared": all players send to and check a shared mailbox.
          Saves are identified by subject: [CIV4PBEM] GameName | filename

    Config:
        smtp_host, smtp_port, smtp_user, smtp_password, smtp_use_tls
        imap_host, imap_port, imap_user, imap_password, imap_use_ssl
        mode: "individual" or "shared"
        shared_email: email address of shared mailbox (only for shared mode)
    """

    def __init__(self, smtp_host: str, smtp_port: int = 587,
                 smtp_user: str = "", smtp_password: str = "",
                 smtp_use_tls: bool = True,
                 imap_host: str = "", imap_port: int = 993,
                 imap_user: str = "", imap_password: str = "",
                 imap_use_ssl: bool = True,
                 mode: str = "shared",
                 shared_email: str = "",
                 from_address: str = ""):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.imap_use_ssl = imap_use_ssl
        self.mode = mode  # "individual" or "shared"
        self.shared_email = shared_email
        self.from_address = from_address or smtp_user
        self._imap: Optional[imaplib.IMAP4_SSL] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Test IMAP connection."""
        try:
            imap = self._get_imap()
            if imap:
                imap.logout()
            self._connected = True
            logger.info(f"Email transport connected (mode={self.mode})")
            return True
        except Exception as e:
            logger.error(f"Email transport connection test failed: {e}")
            self._connected = False
            return False

    def disconnect(self):
        if self._imap:
            try:
                self._imap.logout()
            except Exception:
                pass
            self._imap = None
        self._connected = False

    def _get_imap(self) -> imaplib.IMAP4_SSL:
        """Create and authenticate an IMAP connection."""
        if self.imap_use_ssl:
            imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        else:
            imap = imaplib.IMAP4(self.imap_host, self.imap_port)
        imap.login(self.imap_user, self.imap_password)
        return imap

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

            # Attach save file
            with open(local_path, "rb") as f:
                attachment = MIMEApplication(f.read(), Name=remote_filename)
            attachment["Content-Disposition"] = f'attachment; filename="{remote_filename}"'
            msg.attach(attachment)

            # Send via SMTP
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=60)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=60)

            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email transport: sent {remote_filename} to {recipient}")
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Email transport upload (send) failed: {e}")
            return False

    def download(self, remote_filename: str, local_path: Path, game_name: str) -> bool:
        """Download a specific save file from the mailbox (IMAP).

        Searches for an email with matching subject and attachment filename.
        """
        try:
            imap = self._get_imap()
            imap.select("INBOX")

            # Search for emails with our tag in subject
            search_query = f'(SUBJECT "[CIV4PBEM] {game_name}")'
            status, msg_ids = imap.search(None, search_query)
            if status != "OK" or not msg_ids[0]:
                imap.logout()
                return False

            # Check messages from newest to oldest
            ids = msg_ids[0].split()
            for msg_id in reversed(ids):
                status, data = imap.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(data[0][1])
                subject = self._decode_header(msg.get("Subject", ""))
                parsed_game, parsed_file = self._parse_subject(subject)

                if parsed_file != remote_filename:
                    continue

                # Found the right email - extract attachment
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    fname = part.get_filename()
                    if fname and fname == remote_filename:
                        with open(local_path, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        imap.logout()
                        logger.info(f"Email transport: downloaded {remote_filename}")
                        self._connected = True
                        return True

            imap.logout()
            return False
        except Exception as e:
            logger.error(f"Email transport download (IMAP) failed: {e}")
            return False

    def list_files(self, game_name: str) -> list[str]:
        """List all save file attachments available for a game in the mailbox."""
        try:
            imap = self._get_imap()
            imap.select("INBOX")

            search_query = f'(SUBJECT "[CIV4PBEM] {game_name}")'
            status, msg_ids = imap.search(None, search_query)
            if status != "OK" or not msg_ids[0]:
                imap.logout()
                return []

            files = []
            ids = msg_ids[0].split()
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
            logger.error(f"Email transport list_files (IMAP) failed: {e}")
            return []

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        files = self.list_files(game_name)
        return remote_filename in files

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
        """Delete ALL emails associated with a specific game from the mailbox.

        Searches for emails with subject containing "[CIV4PBEM] {game_name}"
        and marks them for deletion. Does NOT affect other games.

        Returns:
            (success, count_deleted)
        """
        try:
            imap = self._get_imap()
            imap.select("INBOX")

            search_query = f'(SUBJECT "[CIV4PBEM] {game_name}")'
            status, msg_ids = imap.search(None, search_query)
            if status != "OK" or not msg_ids[0]:
                imap.logout()
                return True, 0  # No messages to delete = success

            ids = msg_ids[0].split()
            count = 0
            for msg_id in ids:
                imap.store(msg_id, "+FLAGS", "\\Deleted")
                count += 1

            # Permanently remove flagged messages
            imap.expunge()
            imap.logout()

            logger.info(f"Purged {count} emails for game '{game_name}'")
            return True, count
        except Exception as e:
            logger.error(f"Failed to purge emails for game '{game_name}': {e}")
            return False, 0
