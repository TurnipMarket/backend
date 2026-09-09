import unittest
from unittest.mock import patch, MagicMock
 
from email_sender import EmailService
 
 
class TestEmailService(unittest.TestCase):
 
    def setUp(self):
        self.service = EmailService()
 
    @patch("email_service.smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp_ssl):
        # Simulamos el objeto servidor que devuelve el 'with smtplib.SMTP_SSL(...) as server'
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
 
        result = self.service.send_email(
            to_email="destino@test.com",
            subject="Test",
            html_content="<p>Hola</p>",
        )
 
        self.assertTrue(result)
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
 
    @patch("email_service.smtplib.SMTP_SSL")
    def test_send_email_auth_error(self, mock_smtp_ssl):
        import smtplib
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad credentials")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
 
        result = self.service.send_email(
            to_email="destino@test.com",
            subject="Test",
            html_content="<p>Hola</p>",
        )
 
        self.assertFalse(result)
 
 
if __name__ == "__main__":
    unittest.main()
 
