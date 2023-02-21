from rest_framework import status
from notifier.validators.errors import ErrorResponseException
from notifier.validators import (
    URLValidatorView,
    PayloadValidator
)
from tenants.models import Tenant


class NotificationURLValidatorView(URLValidatorView):
    def validate_tenant_id(self, kwargs):
        tenant_id = self.is_valid_uuid(kwargs.get('tenant_id'))
        if tenant_id is None:
            raise ErrorResponseException(
                'INVALID_TENANT_ID', 
                "Invalid tenant id supplied"
            )
        
        from tenants.models import Tenant
        self.tenant = self.get_or_none(
            Tenant, 
            pk=tenant_id, 
            is_deleted=False
        )
        if self.tenant is None:
            raise ErrorResponseException(
                'INVALID_TENANT_ID', 
                'Invalid tenant ID supplied',
                status.HTTP_404_NOT_FOUND
            )

class NotificationPayloadValidator(PayloadValidator):
    def validate_to(self, to):
        if len(to) == 0:
            raise ErrorResponseException(
                'EMPTY_RECIPIENT_EMAIL', 
                'Invalid recipient email(s) supplied',
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
                tenant=self.context.get('tenant'),
                ref=template_ref, 
                is_enabled=True,
                is_deleted=False
            )
        except Template.DoesNotExist:
            raise ErrorResponseException(
                'INVALID_TEMPLATE_REF', 
                'Invalid template reference supplied',
                status.HTTP_400_BAD_REQUEST
            )
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