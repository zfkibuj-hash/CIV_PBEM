"""
Email notification system using SMTP.
Sends notifications to the next player when a save is uploaded.

Supports:
- Customizable notification templates (subject + body)
- Shared mailbox model: one email account handles both transport and notifications
- Template variables: {game}, {turn}, {from_player}, {to_player}
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# Default templates (used if user doesn't customize)
DEFAULT_SUBJECT_TEMPLATE = "[Civ4 PBEM] {game} - Your turn! (Turn {turn})"
DEFAULT_BODY_TEMPLATE = (
    "Hi {to_player}!\n\n"
    "Player {from_player} finished their turn in game '{game}'.\n"
    "Current turn: {turn}\n\n"
    "It's your turn! Launch Civ4 PBEM Manager to download the save.\n\n"
    "---\n"
    "Sent automatically by Civ4 PBEM Manager\n"
)


class EmailNotifier:
    """Sends email notifications about game turns.

    Can share the same SMTP credentials as the email transport —
    just point notification config to the same host/login.
    Template customization allows users to set their own subject/body.
    """

    def __init__(self, host: str, port: int = 587, username: str = "",
                 password: str = "", use_tls: bool = True,
                 from_address: str = "",
                 subject_template: str = "",
                 body_template: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address or username
        # Custom templates (empty = use defaults)
        self.subject_template = subject_template or DEFAULT_SUBJECT_TEMPLATE
        self.body_template = body_template or DEFAULT_BODY_TEMPLATE

    def send_turn_notification(self, to_email: str, game_name: str,
                                turn_number: int, from_player: str,
                                to_player: str) -> bool:
        """Send notification that it's someone's turn."""
        template_vars = {
            "game": game_name,
            "turn": str(turn_number),
            "from_player": from_player,
            "to_player": to_player,
        }
        try:
            subject = self.subject_template.format(**template_vars)
            body = self.body_template.format(**template_vars)
        except (KeyError, IndexError):
            subject = f"[Civ4 PBEM] {game_name} - Turn {turn_number}"
            body = f"{from_player} finished turn {turn_number} in {game_name}. Your turn, {to_player}!"

        return self._send_email(to_email, subject, body)

    def send_reminder(self, to_email: str, game_name: str,
                      turn_number: int, to_player: str,
                      from_player: str) -> bool:
        """Send a reminder to the current player that it's their turn.

        Template variables same as send_turn_notification.
        Uses reminder_subject_template / reminder_body_template if set,
        otherwise falls back to a default reminder message.
        """
        template_vars = {
            "game": game_name,
            "turn": str(turn_number),
            "from_player": from_player,
            "to_player": to_player,
        }
        subject_tpl = getattr(self, "reminder_subject_template", "") or (
            f"[Civ4 PBEM] {game_name} - Reminder: your turn! (Turn {turn_number})"
        )
        body_tpl = getattr(self, "reminder_body_template", "") or (
            f"Hi {{to_player}}!\n\n"
            f"Just a friendly reminder — it's your turn in game '{{game}}'!\n"
            f"Current turn: {{turn}}\n\n"
            f"Launch Civ4 PBEM Manager to download the save and play.\n\n"
            f"---\nSent automatically by Civ4 PBEM Manager\n"
        )
        try:
            subject = subject_tpl.format(**template_vars)
            body = body_tpl.format(**template_vars)
        except (KeyError, IndexError):
            subject = f"[Civ4 PBEM] {game_name} - Reminder: turn {turn_number}"
            body = f"Reminder: it's your turn, {to_player}! Game: {game_name}, turn {turn_number}."

        return self._send_email(to_email, subject, body)

    def send_game_invite(self, to_email: str, game_name: str,
                          from_player: str) -> bool:
        """Send game invitation."""
        subject = f"[Civ4 PBEM] Game invite: {game_name}"
        body = (
            f"Player {from_player} invites you to a PBEM game!\n\n"
            f"Game name: {game_name}\n\n"
            f"Launch Civ4 PBEM Manager and join the game.\n"
        )
        return self._send_email(to_email, subject, body)

    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email via SMTP."""
        if not self.host:
            logger.warning("SMTP not configured, skipping email")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=30)

            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def test_connection(self) -> tuple[bool, str]:
        """Test SMTP connection. Returns (success, message)."""
        if not self.host:
            return False, "SMTP host not configured"
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)

            server.login(self.username, self.password)
            server.quit()
            return True, "SMTP connection OK"
        except Exception as e:
            return False, f"SMTP error: {e}"
