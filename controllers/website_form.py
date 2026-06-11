import json
import logging

from odoo import _
from odoo.addons.website_crm.controllers.website_form import (
    WebsiteForm as BaseWebsiteForm,
)
from odoo.http import Response, request

_logger = logging.getLogger(__name__)


class WebsiteForm(BaseWebsiteForm):

    def website_form(self, model_name, **kwargs):
        form_data = dict(request.params)
        is_contactus = (
            model_name == 'mail.mail'
            and self._is_union_energy_contactus_form(form_data)
        )
        if not is_contactus:
            return self._ensure_response(
                super().website_form(model_name, **kwargs)
            )

        res = None
        try:
            res = super().website_form(model_name, **kwargs)
        except Exception:
            _logger.exception('Contact Us email submission failed.')

        lead = self._union_energy_create_contactus_lead(form_data)

        if self._response_has_record_id(res):
            return self._ensure_response(res)
        if lead:
            return request.make_json_response({'id': lead.id})
        return self._ensure_response(
            res or json.dumps({'error': _('The form could not be sent.')})
        )

    def _ensure_response(self, result):
        if isinstance(result, Response):
            return result
        return Response.load(result)

    def _union_energy_create_contactus_lead(self, form_data):
        try:
            return request.env['crm.lead']._union_energy_create_from_contactus(form_data)
        except Exception:
            _logger.exception(
                'Failed to create CRM lead from Contact Us form submission.',
            )
            return request.env['crm.lead']

    def _response_payload(self, form_response):
        if not form_response:
            return None
        if isinstance(form_response, Response):
            form_response = form_response.get_data(as_text=True)
        try:
            return json.loads(form_response) if isinstance(form_response, str) else form_response
        except (TypeError, ValueError):
            return None

    def _response_has_record_id(self, form_response):
        data = self._response_payload(form_response)
        return isinstance(data, dict) and bool(data.get('id')) and not data.get('error')

    def _get_http_referer(self):
        httprequest = getattr(request, 'httprequest', None)
        if not httprequest:
            return ''
        headers = getattr(httprequest, 'headers', None)
        if headers:
            return headers.get('Referer', '') or ''
        return (
            getattr(httprequest, 'referrer', None)
            or getattr(httprequest, 'referer', None)
            or ''
        )

    def _is_union_energy_contactus_form(self, form_data):
        referer = self._get_http_referer()
        if '/contactus' in referer:
            return bool(form_data.get('email_from') or form_data.get('name'))
        return (
            'email_to' in form_data
            and form_data.get('subject') is not None
            and form_data.get('description') is not None
            and bool(form_data.get('email_from') or form_data.get('name'))
        )
