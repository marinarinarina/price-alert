"""이메일 발송 (SMTP 기반)"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class Emailer:
    """이메일 발송 클래스"""

    # SMTP 설정 (도메인별)
    SMTP_CONFIG = {
        "gmail.com": {"host": "smtp.gmail.com", "port": 587},
        "naver.com": {"host": "smtp.naver.com", "port": 587},
    }

    def __init__(self, sender_email: str, sender_password: str):
        """
        Args:
            sender_email: 발신자 이메일 (앱 비밀번호 필요)
            sender_password: 앱 비밀번호
        """
        self.sender_email = sender_email
        self.sender_password = sender_password

        # 도메인 추출
        domain = sender_email.split("@")[-1]
        if domain not in self.SMTP_CONFIG:
            raise ValueError(f"지원하지 않는 이메일 도메인: {domain}")

        self.smtp_config = self.SMTP_CONFIG[domain]

    def send(self, recipient: str, subject: str, body: str) -> bool:
        """
        이메일 발송

        Args:
            recipient: 수신자 이메일
            subject: 제목
            body: 본문

        Returns:
            성공 여부
        """
        try:
            # 메시지 생성
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # SMTP 연결 및 발송
            with smtplib.SMTP(
                self.smtp_config["host"], self.smtp_config["port"]
            ) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"[INFO] 이메일 발송 성공: {recipient}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("[ERROR] 이메일 인증 실패 (앱 비밀번호를 확인하세요)")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] 이메일 발송 실패 (SMTP): {e}")
            return False
        except Exception as e:
            print(f"[ERROR] 이메일 발송 실패: {e}")
            return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """이메일 형식 검증"""
        import re

        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))
