import re

from odoo import _, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class CalculatorController(http.Controller):

    def _parse_enquiry_values(self, **kwargs):
        try:
            rooftop_surface_m2 = float(kwargs.get('rooftop_surface_m2', 0))
            monthly_electricity_bill = float(kwargs.get('monthly_electricity_bill', 0))
        except (TypeError, ValueError) as exc:
            raise UserError(_('Invalid numeric values.')) from exc

        phase_type = kwargs.get('phase_type')
        enquiry_type = kwargs.get('enquiry_type')
        if phase_type not in ('single', 'three'):
            raise UserError(_('Please select a valid phase type.'))
        if enquiry_type not in ('residential', 'commercial'):
            raise UserError(_('Please select residential or commercial.'))

        vals = {
            'rooftop_surface_m2': rooftop_surface_m2,
            'monthly_electricity_bill': monthly_electricity_bill,
            'phase_type': phase_type,
            'enquiry_type': enquiry_type,
        }

        contact_name = (kwargs.get('contact_name') or '').strip()
        email = (kwargs.get('email') or '').strip()
        phone = (kwargs.get('phone') or '').strip()
        if contact_name:
            vals['contact_name'] = contact_name
        if email:
            if not _EMAIL_RE.match(email):
                raise UserError(_('Please enter a valid email address.'))
            vals['email'] = email
        if phone:
            vals['phone'] = phone

        return vals

    def _parse_submit_values(self, **kwargs):
        vals = self._parse_enquiry_values(**kwargs)
        for field, label in (
            ('contact_name', _('Contact name')),
            ('email', _('Email')),
            ('phone', _('Phone')),
        ):
            if not vals.get(field):
                raise UserError(_('%(label)s is required.', label=label))
        return vals

    @http.route('/solar-savings-calculator', type='http', auth='public', website=True, sitemap=True)
    def calculator_page(self, **kwargs):
        settings = request.env['calculator.setting'].sudo().get_settings()
        return request.render('union_energy_calculator.calculator_page', {
            'currency_symbol': settings.currency_id.symbol,
        })

    @http.route('/calculator', type='http', auth='public', website=True)
    def calculator_page_redirect(self, **kwargs):
        return request.redirect('/solar-savings-calculator', code=301)

    @http.route('/calculator/calculate', type='json', auth='public', website=True)
    def calculator_calculate(self, **kwargs):
        vals = self._parse_enquiry_values(**kwargs)
        try:
            return request.env['calculator.enquiry'].sudo().compute_pricing_preview(vals)
        except ValidationError as exc:
            raise UserError(str(exc)) from exc

    @http.route('/calculator/submit', type='json', auth='public', website=True)
    def calculator_submit(self, **kwargs):
        vals = self._parse_submit_values(**kwargs)
        Enquiry = request.env['calculator.enquiry'].sudo()
        try:
            enquiry = Enquiry.create(vals)
            enquiry.action_create_lead()
        except ValidationError as exc:
            raise UserError(str(exc)) from exc

        payload = enquiry._public_pricing_payload()
        payload.update({
            'enquiry_id': enquiry.id,
            'lead_id': enquiry.lead_id.id,
        })
        return payload
