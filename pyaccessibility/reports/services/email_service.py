from typing import Union
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class EmailService:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_report(
        self,
        to_email: str,
        subject: str,
        body: str,
        report_content: Union[str, bytes],
        report_format: str = "html"
    ) -> None:
        """Send accessibility report via email."""
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = to_email
        msg["Subject"] = subject

        # Add email body
        msg.attach(MIMEText(body, "plain"))

        # Attach report
        filename = f"accessibility_report.{report_format}"
        attachment: Union[MIMEText, MIMEApplication]
        if isinstance(report_content, str):
            attachment = MIMEText(report_content, report_format)
        else:  # bytes (PDF)
            attachment = MIMEApplication(report_content, _subtype="pdf")

        attachment.add_header(
            "Content-Disposition", "attachment", filename=filename
        )
        msg.attach(attachment)

        # Send email
        await aiosmtplib.send(
            msg,
            hostname=self.smtp_host,
            port=self.smtp_port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls
        )
