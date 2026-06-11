from odoo import _, api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    calculator_enquiry_id = fields.Many2one(
        'calculator.enquiry',
        string='Calculator Enquiry',
        readonly=True,
        copy=False,
    )
    calculator_rooftop_surface_m2 = fields.Float(
        string='Rooftop Surface (m²)',
        readonly=True,
        copy=False,
    )
    calculator_monthly_bill = fields.Monetary(
        string='Monthly Bill',
        currency_field='company_currency',
        readonly=True,
        copy=False,
    )
    calculator_phase_type = fields.Selection(
        [
            ('single', 'Single Phase'),
            ('three', 'Three Phase'),
        ],
        string='Phase Type',
        readonly=True,
        copy=False,
    )
    calculator_enquiry_type = fields.Selection(
        [
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
        ],
        string='Enquiry Type',
        readonly=True,
        copy=False,
    )
    calculator_estimated_kwh = fields.Float(
        string='Est. Consumption (kWh)',
        readonly=True,
        copy=False,
    )
    calculator_solar_yield_kwh = fields.Float(
        string='Solar Yield (kWh)',
        readonly=True,
        copy=False,
    )
    calculator_cost_efficiency_pct = fields.Float(
        string='Cost Efficiency (%)',
        readonly=True,
        copy=False,
    )
    calculator_monthly_savings = fields.Monetary(
        string='Monthly Savings',
        currency_field='company_currency',
        readonly=True,
        copy=False,
    )

    @api.model
    def _union_energy_create_from_contactus(self, form_data):
        from odoo.http import request

        contact_name = (form_data.get('name') or '').strip()
        email_from = (form_data.get('email_from') or '').strip()
        phone = (form_data.get('phone') or '').strip()
        partner_name = (form_data.get('company') or '').strip()
        subject = (form_data.get('subject') or '').strip()
        description = (form_data.get('description') or '').strip()

        if not contact_name and not email_from:
            return self.env['crm.lead']

        lead_name = subject or _(
            'Contact Us - %(contact)s',
            contact=contact_name or email_from,
        )

        lead_vals = {
            'name': lead_name,
            'contact_name': contact_name or email_from,
            'email_from': email_from,
            'phone': phone,
            'partner_name': partner_name,
            'description': description,
            'type': 'opportunity',
        }

        website = getattr(request, 'website', None)
        if website and website.company_id:
            lead_vals['company_id'] = website.company_id.id
        else:
            lead_vals['company_id'] = self.env.company.id

        medium = self.env['utm.medium']._fetch_or_create_utm_medium('website')
        if medium:
            lead_vals['medium_id'] = medium.id

        tag = self.env.ref(
            'union_energy_calculator.crm_tag_website_contactus',
            raise_if_not_found=False,
        )
        if tag:
            lead_vals['tag_ids'] = [(4, tag.id)]

        filter_method = getattr(self, 'website_form_input_filter', None)
        if filter_method:
            try:
                lead_vals = filter_method(request, lead_vals)
            except Exception:
                pass

        return self.sudo().create(lead_vals)
