from rest_framework import status
from notifier.validators.errors import ErrorResponseException
from notifier.validators import (
    URLValidatorView,
    PayloadValidator
)


class NotificationURLValidatorView(URLValidatorView):
    pass

class NotificationPayloadValidator(PayloadValidator):
    def validate_to(self, to):
        if len(to) == 0:
            raise ErrorResponseException(
                'EMPTY_RECIPIENT_EMAIL', 
                'Empty recipient email(s)',
                status.HTTP_400_BAD_REQUEST
            )

        for email in to:
            if self.is_valid_email(email) == False:
                raise ErrorResponseException(
                    'INVALID_RECIPIENT_EMAIL', 
                    'Invalid recipient email(s) supplied',
                    status.HTTP_400_BAD_REQUEST
                )
        self.validated_data['to'] = to
        if self.instance is not None:
            self.instance.to = to
    
    def validate_template_ref(self, template_ref):
        try:
            from templates.models import Template
            self.template = Template.objects.get(
                ref=template_ref, 
                is_enabled=True,
                is_deleted=False
            )
        except Template.DoesNotExist:
            raise ErrorResponseException(
                'INVALID_TEMPLATE_REF', 'Invalid template reference supplied',
                status.HTTP_400_BAD_REQUEST)
        self.validated_data['template_ref'] = template_ref
        if self.instance is not None:
            self.instance.template_ref = template_ref

    def validate_cc(self, cc):
        if len(cc) > 0:
            for email in cc:
                if self.is_valid_email(email) == False:
                    raise ErrorResponseException(
                        'INVALID_CC_RECIPIENT_EMAIL', 
                        'Invalid CC recipient email(s) supplied',
                        status.HTTP_400_BAD_REQUEST
                    )
        self.validated_data['cc'] = cc
        if self.instance is not None:
            self.instance.cc = cc

    def validate_bcc(self, bcc):
        if len(bcc) > 0:
            for email in bcc:
                if self.is_valid_email(email) == False:
                    raise ErrorResponseException(
                        'INVALID_BCC_RECIPIENT_EMAIL', 
                        'Invalid BCC recipient email(s) supplied',
                        status.HTTP_400_BAD_REQUEST
                    )
        self.validated_data['bcc'] = bcc
        if self.instance is not None:
            self.instance.bcc = bcc

    def validate_subject(self, subject):
        if len(subject) == 0:
            raise ErrorResponseException(
                'INVALID_EMAIL_SUBJECT', 
                'Invalid email subject supplied',
                status.HTTP_400_BAD_REQUEST
            )
                    
        self.validated_data['subject'] = subject
        if self.instance is not None:
            self.instance.subject = subject