"""
Email notification system using SMTP.
Sends notifications to the next player when a save is uploaded.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends email notifications about game turns."""

    def __init__(self, host: str, port: int = 587, username: str = "",
                 password: str = "", use_tls: bool = True,
                 from_address: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address or username

    def send_turn_notification(self, to_email: str, game_name: str,
                                turn_number: int, from_player: str,
                                to_player: str) -> bool:
        """Send notification that it's someone's turn."""
        subject = f"[Civ4 PBEM] {game_name} - Twoja kolej! (Tura {turn_number})"
        body = self._build_turn_body(game_name, turn_number, from_player, to_player)
        return self._send_email(to_email, subject, body)

    def send_game_invite(self, to_email: str, game_name: str,
                          from_player: str) -> bool:
        """Send game invitation."""
        subject = f"[Civ4 PBEM] Zaproszenie do gry: {game_name}"
        body = (
            f"Gracz {from_player} zaprasza Cie do gry PBEM!\n\n"
            f"Nazwa gry: {game_name}\n\n"
            f"Uruchom Civ4 PBEM Manager i dolacz do gry.\n"
        )
        return self._send_email(to_email, subject, body)

    def _build_turn_body(self, game_name: str, turn_number: int,
                          from_player: str, to_player: str) -> str:
        return (
            f"Czesc {to_player}!\n\n"
            f"Gracz {from_player} zakonczyl swoja ture w grze '{game_name}'.\n"
            f"Aktualna tura: {turn_number}\n\n"
            f"Twoja kolej! Uruchom Civ4 PBEM Manager aby pobrac save.\n\n"
            f"---\n"
            f"Wiadomosc wyslana automatycznie przez Civ4 PBEM Manager\n"
        )

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
            return True, "Polaczenie SMTP OK"
        except Exception as e:
            return False, f"Blad SMTP: {e}"
