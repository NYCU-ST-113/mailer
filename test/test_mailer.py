# test_mailer_service.py
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import the modules to test
from mailer_service.main import (
    app, EmailConfig, EmailSender, TemplateManager, 
    template_manager, email_sender, email_config,
    EmailRequest, TemplateEmailRequest, ApplicationCreatedRequest,
    ApplicationRejectedRequest, ApplicationApprovedRequest,
    ApplicationDeletedRequest, PaymentCreatedRequest,
    PaymentSuccessRequest, PaymentFailedRequest,
    TEMPLATE_DIR
)

class TestEmailConfig:
    """Test EmailConfig class"""
    
    def test_email_config_default_values(self):
        """Test EmailConfig with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = EmailConfig()
            assert config.smtp_server == "sandbox.smtp.mailtrap.io"
            assert config.smtp_port == 2525
            assert config.smtp_username == ""
            assert config.smtp_password == ""
            assert config.default_sender == "payment@example.com"
    
    def test_email_config_custom_values(self):
        """Test EmailConfig with custom environment variables"""
        env_vars = {
            "SMTP_SERVER": "'custom.smtp.com'",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "'test_user'",
            "SMTP_PASSWORD": "'test_pass'",
            "DEFAULT_SENDER": "custom@example.com"
        }
        with patch.dict(os.environ, env_vars):
            config = EmailConfig()
            assert config.smtp_server == "custom.smtp.com"
            assert config.smtp_port == 587
            assert config.smtp_username == "test_user"
            assert config.smtp_password == "test_pass"
            assert config.default_sender == "custom@example.com"
    
    def test_email_config_strip_quotes(self):
        """Test that quotes are stripped from environment variables"""
        env_vars = {
            "SMTP_SERVER": "'quoted.server.com'",
            "SMTP_USERNAME": "'quoted_user'",
            "SMTP_PASSWORD": "'quoted_pass'"
        }
        with patch.dict(os.environ, env_vars):
            config = EmailConfig()
            assert config.smtp_server == "quoted.server.com"
            assert config.smtp_username == "quoted_user"
            assert config.smtp_password == "quoted_pass"


class TestEmailSender:
    """Test EmailSender class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config = EmailConfig()
        self.sender = EmailSender(self.config)
    
    def test_email_sender_init_with_config(self):
        """Test EmailSender initialization with config"""
        config = EmailConfig()
        sender = EmailSender(config)
        assert sender.config == config
    
    def test_email_sender_init_without_config(self):
        """Test EmailSender initialization without config"""
        sender = EmailSender()
        assert isinstance(sender.config, EmailConfig)
    
    def test_send_email_no_recipients(self):
        """Test send_email with no recipients"""
        result = self.sender.send_email(
            to_emails=[],
            subject="Test",
            html_content="<p>Test</p>"
        )
        assert result is False
    
    def test_send_email_none_recipients(self):
        """Test send_email with None recipients"""
        result = self.sender.send_email(
            to_emails=None,
            subject="Test",
            html_content="<p>Test</p>"
        )
        assert result is False
    
    @patch.dict(os.environ, {"TESTING": "True"})
    def test_send_email_test_mode(self):
        """Test send_email in test mode"""
        result = self.sender.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>"
        )
        assert result is True
    
    @patch('smtplib.SMTP')
    def test_send_email_success_single_recipient(self, mock_smtp):
        """Test successful email sending with single recipient"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.sender.send_email(
            to_emails="test@example.com",
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test Text"
        )
        
        assert result is True
        mock_smtp.assert_called_once_with(self.config.smtp_server, self.config.smtp_port, timeout=30)
        mock_server.set_debuglevel.assert_called_once_with(1)
        mock_server.ehlo.assert_called()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(self.config.smtp_username, self.config.smtp_password)
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_success_multiple_recipients(self, mock_smtp):
        """Test successful email sending with multiple recipients"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.sender.send_email(
            to_emails=["test1@example.com", "test2@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>"
        )
        
        assert result is True
        mock_server.sendmail.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_with_cc_bcc(self, mock_smtp):
        """Test email sending with CC and BCC"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.sender.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            from_email="custom@example.com"
        )
        
        assert result is True
        # Verify that sendmail was called with all recipients
        args, kwargs = mock_server.sendmail.call_args
        all_recipients = args[1]
        assert "test@example.com" in all_recipients
        assert "cc@example.com" in all_recipients
        assert "bcc@example.com" in all_recipients
    
    @patch('smtplib.SMTP')
    def test_send_email_with_cc_bcc_strings(self, mock_smtp):
        """Test email sending with CC and BCC as strings"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.sender.send_email(
            to_emails="test@example.com",
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            cc="cc@example.com",
            bcc="bcc@example.com"
        )
        
        assert result is True
    
    @patch('smtplib.SMTP')
    def test_send_email_no_text_content(self, mock_smtp):
        """Test email sending without text content"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.sender.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>"
        )
        
        assert result is True
    
    @patch('smtplib.SMTP')
    def test_send_email_smtp_exception(self, mock_smtp):
        """Test email sending with SMTP exception"""
        mock_smtp.side_effect = smtplib.SMTPException("SMTP Error")
        
        result = self.sender.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>"
        )
        
        assert result is False
    
    @patch('smtplib.SMTP')
    def test_send_email_general_exception(self, mock_smtp):
        """Test email sending with general exception"""
        mock_smtp.side_effect = Exception("General Error")
        
        result = self.sender.send_email(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>"
        )
        
        assert result is False


class TestTemplateManager:
    """Test TemplateManager class"""
    
    def setup_method(self):
        """Setup for each test"""
        # Create a temporary directory for templates
        self.temp_dir = tempfile.mkdtemp()
        self.original_template_dir = TEMPLATE_DIR
        
        # Patch TEMPLATE_DIR
        self.template_manager = TemplateManager()
    
    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_template_manager_init(self):
        """Test TemplateManager initialization"""
        tm = TemplateManager()
        assert isinstance(tm.templates, dict)
        assert "payment_created" in tm.templates
        assert "payment_success" in tm.templates
        assert "payment_failed" in tm.templates
        assert "application_created" in tm.templates
        assert "application_approved" in tm.templates
        assert "application_rejected" in tm.templates
        assert "application_deleted" in tm.templates
    
    def test_get_template_subject_existing(self):
        """Test getting subject for existing template"""
        subject = self.template_manager.get_template_subject("payment_created")
        assert "Payment Created" in subject
        assert "{{payment_id}}" in subject
    
    def test_get_template_subject_non_existing(self):
        """Test getting subject for non-existing template"""
        subject = self.template_manager.get_template_subject("non_existing")
        assert subject == "Notification"
    
    def test_render_template_success(self):
        """Test successful template rendering"""
        template_data = {
            "payment_id": "PAY123",
            "service_name": "Test Service",
            "amount": "100.00"
        }
        
        html_content, text_content = self.template_manager.render_template(
            "payment_created", template_data
        )
        
        assert "PAY123" in html_content
        assert "Test Service" in html_content
        assert "100.00" in html_content
        assert isinstance(text_content, str)
    
    def test_render_template_with_conditional(self):
        """Test template rendering with conditional content"""
        template_data = {
            "payment_id": "PAY123",
            "service_name": "Test Service",
            "amount": "100.00",
            "due_date": "2024-12-31"
        }
        
        html_content, text_content = self.template_manager.render_template(
            "payment_created", template_data
        )
        
        assert "2024-12-31" in html_content
    
    def test_render_template_without_conditional(self):
        """Test template rendering without conditional content"""
        template_data = {
            "payment_id": "PAY123",
            "service_name": "Test Service",
            "amount": "100.00"
        }
        
        html_content, text_content = self.template_manager.render_template(
            "payment_created", template_data
        )
        
        # Should not contain due date section when due_date is not provided
        assert html_content is not None
    
    @patch('mailer_service.main.template_env.get_template')
    def test_render_template_html_error(self, mock_get_template):
        """Test template rendering with HTML template error"""
        mock_get_template.side_effect = Exception("Template not found")
        
        with pytest.raises(Exception) as exc_info:
            self.template_manager.render_template("non_existing", {})
        
        assert "Template rendering error" in str(exc_info.value)
    
    @patch('mailer_service.main.template_env.get_template')
    def test_render_template_text_fallback(self, mock_get_template):
        """Test template rendering with text template fallback"""
        def side_effect(template_name):
            if template_name.endswith('.txt'):
                raise Exception("Text template not found")
            return Mock(render=Mock(return_value="<html>Test</html>"))
        
        mock_get_template.side_effect = side_effect
        
        html_content, text_content = self.template_manager.render_template(
            "test_template", {}
        )
        
        assert html_content == "<html>Test</html>"
        assert "HTML-compatible email client" in text_content


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def setup_method(self):
        """Setup for each test"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "email-service"
    
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_email_endpoint_success(self, mock_send_email):
        """Test successful email sending endpoint"""
        mock_send_email.return_value = True
        
        email_data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test Body",
            "html_body": "<p>Test HTML</p>",
            "source_service": "test-service"
        }
        
        response = self.client.post("/send", json=email_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Email sent successfully"
        
        mock_send_email.assert_called_once_with(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test Body",
            from_email=None,
            cc=None,
            bcc=None
        )
    
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_email_endpoint_no_html_body(self, mock_send_email):
        """Test email sending endpoint without HTML body"""
        mock_send_email.return_value = True
        
        email_data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test Body",
            "source_service": "test-service"
        }
        
        response = self.client.post("/send", json=email_data)
        assert response.status_code == 200
        
        mock_send_email.assert_called_once_with(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="Test Body",  # body used as html_content when html_body is None
            text_content="Test Body",
            from_email=None,
            cc=None,
            bcc=None
        )
    
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_email_endpoint_with_optional_fields(self, mock_send_email):
        """Test email sending endpoint with all optional fields"""
        mock_send_email.return_value = True
        
        email_data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test Body",
            "html_body": "<p>Test HTML</p>",
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "sender": "sender@example.com",
            "source_service": "test-service"
        }
        
        response = self.client.post("/send", json=email_data)
        assert response.status_code == 200
        
        mock_send_email.assert_called_once_with(
            to_emails=["test@example.com"],
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test Body",
            from_email="sender@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
    
    @patch('mailer_service.main.template_manager.render_template')
    @patch('mailer_service.main.template_manager.get_template_subject')
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_template_email_endpoint_success(self, mock_send_email, mock_get_subject, mock_render):
        """Test successful template email sending endpoint"""
        mock_render.return_value = ("<p>Rendered HTML</p>", "Rendered Text")
        mock_get_subject.return_value = "Template Subject: {{payment_id}}"
        mock_send_email.return_value = True
        
        template_data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123", "amount": "100.00"},
            "source_service": "test-service"
        }
        
        response = self.client.post("/send-template", json=template_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Template email sent successfully"
        
        mock_render.assert_called_once_with(
            template_id="payment_created", 
            template_data={"payment_id": "PAY123", "amount": "100.00"}
        )
        mock_send_email.assert_called_once()
    
    @patch('mailer_service.main.template_manager.render_template')
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_template_email_endpoint_send_failure(self, mock_send_email, mock_render):
        """Test template email endpoint with send failure"""
        mock_render.return_value = ("<p>Rendered HTML</p>", "Rendered Text")
        mock_send_email.return_value = False
        
        template_data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123"},
            "source_service": "test-service"
        }
        
        response = self.client.post("/send-template", json=template_data)
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Error processing template: 500: Failed to send template email"

   
    @patch('mailer_service.main.template_manager.render_template')
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_template_email_endpoint_custom_subject(self, mock_send_email, mock_render):
        """Test template email endpoint with custom subject"""
        mock_render.return_value = ("<p>Rendered HTML</p>", "Rendered Text")
        mock_send_email.return_value = True
        
        template_data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123"},
            "subject": "Custom Subject",
            "source_service": "test-service"
        }
        
        response = self.client.post("/send-template", json=template_data)
        assert response.status_code == 200
        
        # Verify send_email was called with custom subject
        args, kwargs = mock_send_email.call_args
        assert kwargs["subject"] == "Custom Subject"
    
    @patch('mailer_service.main.template_manager.render_template')
    @patch('mailer_service.main.template_manager.get_template_subject')
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_template_email_endpoint_subject_replacement(self, mock_send_email, mock_get_subject, mock_render):
        """Test template email endpoint with subject variable replacement"""
        mock_render.return_value = ("<p>Rendered HTML</p>", "Rendered Text")
        mock_get_subject.return_value = "Payment: {{payment_id}} - {{amount}}"
        mock_send_email.return_value = True
        
        template_data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123", "amount": "100.00"},
            "source_service": "test-service"
        }
        
        response = self.client.post("/send-template", json=template_data)
        assert response.status_code == 200
        
        # Verify subject variables were replaced
        args, kwargs = mock_send_email.call_args
        assert kwargs["subject"] == "Payment: PAY123 - 100.00"
    
    @patch('mailer_service.main.template_manager.render_template')
    @patch('mailer_service.main.email_sender.send_email')
    def test_send_template_email_endpoint_with_optional_fields(self, mock_send_email, mock_render):
        """Test template email endpoint with optional fields"""
        mock_render.return_value = ("<p>Rendered HTML</p>", "Rendered Text")
        mock_send_email.return_value = True
        
        template_data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123"},
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "sender": "sender@example.com",
            "source_service": "test-service"
        }
        
        response = self.client.post("/send-template", json=template_data)
        assert response.status_code == 200
        
        mock_send_email.assert_called_once_with(
            to_emails=["test@example.com"],
            subject=mock_send_email.call_args[1]["subject"],
            html_content="<p>Rendered HTML</p>",
            text_content="Rendered Text",
            from_email="sender@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
    
    @patch('mailer_service.main.template_manager.render_template')
    def test_send_template_email_endpoint_render_error(self, mock_render):
        """Test template email endpoint with rendering error"""
        mock_render.side_effect = Exception("Template error")
        
        template_data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123"},
            "source_service": "test-service"
        }
        
        response = self.client.post("/send-template", json=template_data)
        assert response.status_code == 500
        data = response.json()
        assert "Error processing template" in data["detail"]

class TestPydanticModels:
    """Test Pydantic models"""
    
    def test_email_request_model(self):
        """Test EmailRequest model"""
        data = {
            "to": ["test@example.com"],
            "subject": "Test",
            "body": "Test body",
            "source_service": "test-service"
        }
        request = EmailRequest(**data)
        assert request.to == ["test@example.com"]
        assert request.subject == "Test"
        assert request.body == "Test body"
        assert request.source_service == "test-service"
        assert request.html_body is None
        assert request.cc is None
        assert request.bcc is None
        assert request.sender is None
        assert request.attachments is None
    
    def test_email_request_model_with_optional_fields(self):
        """Test EmailRequest model with optional fields"""
        data = {
            "to": ["test@example.com"],
            "subject": "Test",
            "body": "Test body",
            "html_body": "<p>HTML body</p>",
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "sender": "sender@example.com",
            "source_service": "test-service",
            "attachments": [{"name": "file.txt", "content": "content"}]
        }
        request = EmailRequest(**data)
        assert request.html_body == "<p>HTML body</p>"
        assert request.cc == ["cc@example.com"]
        assert request.bcc == ["bcc@example.com"]
        assert request.sender == "sender@example.com"
        assert request.attachments == [{"name": "file.txt", "content": "content"}]
    
    def test_template_email_request_model(self):
        """Test TemplateEmailRequest model"""
        data = {
            "to": ["test@example.com"],
            "template_id": "payment_created",
            "template_data": {"payment_id": "PAY123"},
            "source_service": "test-service"
        }
        request = TemplateEmailRequest(**data)
        assert request.to == ["test@example.com"]
        assert request.template_id == "payment_created"
        assert request.template_data == {"payment_id": "PAY123"}
        assert request.source_service == "test-service"
        assert request.subject is None
        assert request.cc is None
        assert request.bcc is None
        assert request.sender is None
    
    def test_application_created_request_model(self):
        """Test ApplicationCreatedRequest model"""
        data = {
            "recipient": "test@example.com",
            "application_id": "APP123",
            "service_name": "Test Service",
            "amount": 100.50
        }
        request = ApplicationCreatedRequest(**data)
        assert request.recipient == "test@example.com"
        assert request.application_id == "APP123"
        assert request.service_name == "Test Service"
        assert request.amount == 100.50
    
    def test_application_rejected_request_model(self):
        """Test ApplicationRejectedRequest model"""
        data = {
            "recipient": "test@example.com",
            "application_id": "APP123",
            "service_name": "Test Service",
            "amount": 100.50,
            "reason": "Insufficient funds"
        }
        request = ApplicationRejectedRequest(**data)
        assert request.reason == "Insufficient funds"
    
    def test_application_approved_request_model(self):
        """Test ApplicationApprovedRequest model"""
        data = {
            "recipient": "test@example.com",
            "application_id": "APP123",
            "service_name": "Test Service",
            "amount": 100.50,
            "payment_id": "PAY123"
        }
        request = ApplicationApprovedRequest(**data)
        assert request.payment_id == "PAY123"
    
    def test_application_deleted_request_model(self):
        """Test ApplicationDeletedRequest model"""
        data = {
            "recipient": "test@example.com",
            "application_id": "APP123",
            "service_name": "Test Service",
            "amount": 100.50
        }
        request = ApplicationDeletedRequest(**data)
        assert request.recipient == "test@example.com"
    
    def test_payment_created_request_model(self):
        """Test PaymentCreatedRequest model"""
        data = {
            "recipient": "test@example.com",
            "payment_id": "PAY123",
            "service_name": "Test Service",
            "amount": 100.50
        }
        request = PaymentCreatedRequest(**data)
        assert request.due_date is None
        
        # Test with due_date
        data["due_date"] = "2024-12-31"
        request = PaymentCreatedRequest(**data)
        assert request.due_date == "2024-12-31"
    
    def test_payment_success_request_model(self):
        """Test PaymentSuccessRequest model"""
        data = {
            "recipient": "test@example.com",
            "payment_id": "PAY123",
            "service_name": "Test Service",
            "amount": 100.50
        }
        request = PaymentSuccessRequest(**data)
        assert request.transaction_id is None
        
        # Test with transaction_id
        data["transaction_id"] = "TXN123"
        request = PaymentSuccessRequest(**data)
        assert request.transaction_id == "TXN123"
    
    def test_payment_failed_request_model(self):
        """Test PaymentFailedRequest model"""
        data = {
            "recipient": "test@example.com",
            "payment_id": "PAY123",
            "service_name": "Test Service",
            "amount": 100.50,
            "reason": "Card declined"
        }
        request = PaymentFailedRequest(**data)
        assert request.reason == "Card declined"


class TestGlobalVariables:
    """Test global variables and initialization"""
    
    def test_global_email_config(self):
        """Test global email_config variable"""
        assert isinstance(email_config, EmailConfig)
    
    def test_global_email_sender(self):
        """Test global email_sender variable"""
        assert isinstance(email_sender, EmailSender)
        assert email_sender.config == email_config


