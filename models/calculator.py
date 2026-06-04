import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class CalculatorSetting(models.Model):
    _name = 'calculator.setting'
    _description = 'Calculator Setting'

    name = fields.Char(default='Calculator Settings')
    price_per_kwh = fields.Float(string='Price per kWh', default=0.30)
    kwh_yield_per_m2 = fields.Float(
        string='Solar Yield per m² (kWh/month)',
        default=15.0,
        help='Estimated monthly solar energy yield per square metre of rooftop.',
    )
    install_price_per_m2 = fields.Monetary(
        string='Installation Price per m²',
        currency_field='currency_id',
        default=800.0,
        help='Used to compute expected revenue on CRM opportunities.',
    )

    residential_multiplier = fields.Float(default=1.0)
    commercial_multiplier = fields.Float(default=1.15)
    single_phase_surcharge = fields.Monetary(currency_field='currency_id')
    three_phase_surcharge = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.model
    def get_settings(self):
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({'name': _('Calculator Settings')})
        return settings

    @api.constrains('price_per_kwh', 'kwh_yield_per_m2', 'install_price_per_m2')
    def _check_positive_settings(self):
        for record in self:
            if record.price_per_kwh <= 0:
                raise ValidationError(_('Price per kWh must be greater than zero.'))
            if record.kwh_yield_per_m2 <= 0:
                raise ValidationError(
                    _('Solar yield per m² must be greater than zero.')
                )
            if record.install_price_per_m2 < 0:
                raise ValidationError(
                    _('Installation price per m² cannot be negative.')
                )


class CalculatorEnquiry(models.Model):
    _name = 'calculator.enquiry'
    _description = 'Calculator Enquiry'
    _order = 'create_date desc'

    name = fields.Char(compute='_compute_name', store=True)
    contact_name = fields.Char(string='Contact Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)
    rooftop_surface_m2 = fields.Float(
        string='Surface of the Rooftop (m2)',
        required=True,
    )
    monthly_electricity_bill = fields.Monetary(
        string='Monthly Electricity Bill (SGD)',
        currency_field='currency_id',
        required=True,
    )
    phase_type = fields.Selection(
        [
            ('single', 'Single Phase'),
            ('three', 'Three Phase'),
        ],
        string='Phase Type',
        required=True,
        default='single',
    )
    enquiry_type = fields.Selection(
        [
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
        ],
        string='Enquiry Type',
        required=True,
        default='residential',
    )
    estimated_kwh = fields.Float(compute='_compute_pricing', store=True)
    estimated_price = fields.Monetary(
        compute='_compute_pricing',
        store=True,
        currency_field='currency_id',
    )
    solar_yield_kwh = fields.Float(
        string='Solar Yield (kWh)',
        compute='_compute_pricing',
        store=True,
    )
    cost_efficiency_pct = fields.Float(
        string='Cost Efficiency (%)',
        compute='_compute_pricing',
        store=True,
    )
    monthly_savings = fields.Monetary(
        string='Monthly Savings',
        compute='_compute_pricing',
        store=True,
        currency_field='currency_id',
    )
    expected_revenue = fields.Monetary(
        string='Expected Revenue',
        compute='_compute_pricing',
        store=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env['calculator.setting'].get_settings().currency_id,
    )
    lead_id = fields.Many2one('crm.lead', string='CRM Lead', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        settings = self.env['calculator.setting'].get_settings()
        for vals in vals_list:
            vals.setdefault('currency_id', settings.currency_id.id)
        return super().create(vals_list)

    @api.depends('contact_name', 'enquiry_type', 'monthly_electricity_bill')
    def _compute_name(self):
        for record in self:
            enquiry_label = dict(
                record._fields['enquiry_type'].selection
            ).get(record.enquiry_type, '')
            contact = record.contact_name or _('Anonymous')
            record.name = _(
                '%(type)s enquiry - %(contact)s',
                type=enquiry_label,
                contact=contact,
            )

    def _get_phase_fee(self, settings):
        self.ensure_one()
        return (
            settings.single_phase_surcharge
            if self.phase_type == 'single'
            else settings.three_phase_surcharge
        )

    @api.depends(
        'rooftop_surface_m2',
        'monthly_electricity_bill',
        'enquiry_type',
        'phase_type',
    )
    def _compute_pricing(self):
        settings = self.env['calculator.setting'].get_settings()
        for record in self:
            phase_fee = record._get_phase_fee(settings)

            if settings.price_per_kwh <= 0:
                record.estimated_kwh = 0.0
                record.estimated_price = 0.0
                record.solar_yield_kwh = 0.0
                record.cost_efficiency_pct = 0.0
                record.monthly_savings = 0.0
                record.expected_revenue = phase_fee
                continue

            record.estimated_kwh = (
                record.monthly_electricity_bill / settings.price_per_kwh
            )
            multiplier = (
                settings.residential_multiplier
                if record.enquiry_type == 'residential'
                else settings.commercial_multiplier
            )
            record.estimated_price = (
                record.monthly_electricity_bill * multiplier + phase_fee
            )

            record.solar_yield_kwh = (
                record.rooftop_surface_m2 * settings.kwh_yield_per_m2
            )
            if record.estimated_kwh > 0:
                record.cost_efficiency_pct = min(
                    100.0,
                    (record.solar_yield_kwh / record.estimated_kwh) * 100.0,
                )
            else:
                record.cost_efficiency_pct = 0.0

            offset_kwh = min(record.solar_yield_kwh, record.estimated_kwh)
            record.monthly_savings = offset_kwh * settings.price_per_kwh
            record.expected_revenue = (
                record.rooftop_surface_m2 * settings.install_price_per_m2
                + phase_fee
            )

    def _public_pricing_payload(self):
        self.ensure_one()
        return {
            'estimated_kwh': self.estimated_kwh,
            'solar_yield_kwh': self.solar_yield_kwh,
            'cost_efficiency_pct': self.cost_efficiency_pct,
            'monthly_savings': self.monthly_savings,
            'currency_id': self.currency_id.id,
            'currency_symbol': self.currency_id.symbol,
        }

    @api.model
    def compute_pricing_preview(self, vals):
        settings = self.env['calculator.setting'].get_settings()
        enquiry = self.new(vals)
        enquiry.currency_id = settings.currency_id
        enquiry._compute_pricing()
        return enquiry._public_pricing_payload()

    @api.constrains('rooftop_surface_m2', 'monthly_electricity_bill')
    def _check_input_values(self):
        for record in self:
            if record.rooftop_surface_m2 <= 0:
                raise ValidationError(
                    _('Surface of the Rooftop must be greater than zero.')
                )
            if record.monthly_electricity_bill < 0:
                raise ValidationError(
                    _('Monthly Electricity Bill cannot be negative.')
                )

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and not _EMAIL_RE.match(record.email.strip()):
                raise ValidationError(_('Please enter a valid email address.'))

    def action_create_lead(self):
        self.ensure_one()
        if self.lead_id:
            return self.lead_id

        phase_label = dict(self._fields['phase_type'].selection).get(
            self.phase_type, ''
        )
        enquiry_label = dict(self._fields['enquiry_type'].selection).get(
            self.enquiry_type, ''
        )
        description = _(
            'Contact: %(contact)s\n'
            'Email: %(email)s\n'
            'Phone: %(phone)s\n'
            'Enquiry type: %(etype)s\n'
            'Rooftop surface: %(surface)s m2\n'
            'Monthly electricity bill: %(bill)s %(currency)s\n'
            'Phase type: %(phase)s\n'
            'Estimated consumption: %(kwh)s kWh\n'
            'Solar yield: %(solar)s kWh\n'
            'Cost efficiency: %(efficiency)s%%\n'
            'Monthly savings: %(savings)s %(currency)s\n'
            'Expected revenue: %(revenue)s %(currency)s',
            contact=self.contact_name,
            email=self.email,
            phone=self.phone,
            etype=enquiry_label,
            surface=self.rooftop_surface_m2,
            bill=self.monthly_electricity_bill,
            currency=self.currency_id.name,
            phase=phase_label,
            kwh=round(self.estimated_kwh, 2),
            solar=round(self.solar_yield_kwh, 2),
            efficiency=round(self.cost_efficiency_pct, 1),
            savings=round(self.monthly_savings, 2),
            revenue=round(self.expected_revenue, 2),
        )
        tag = self.env.ref(
            'union_energy_calculator.crm_tag_website_calculator',
            raise_if_not_found=False,
        )
        lead_vals = {
            'name': _(
                '%(type)s Energy Enquiry - %(contact)s',
                type=enquiry_label,
                contact=self.contact_name,
            ),
            'description': description,
            'type': 'opportunity',
            'contact_name': self.contact_name,
            'email_from': self.email,
            'phone': self.phone,
            'expected_revenue': self.expected_revenue,
            'calculator_enquiry_id': self.id,
            'calculator_rooftop_surface_m2': self.rooftop_surface_m2,
            'calculator_monthly_bill': self.monthly_electricity_bill,
            'calculator_phase_type': self.phase_type,
            'calculator_enquiry_type': self.enquiry_type,
            'calculator_estimated_kwh': self.estimated_kwh,
            'calculator_solar_yield_kwh': self.solar_yield_kwh,
            'calculator_cost_efficiency_pct': self.cost_efficiency_pct,
            'calculator_monthly_savings': self.monthly_savings,
        }
        if tag:
            lead_vals['tag_ids'] = [(4, tag.id)]
        lead = self.env['crm.lead'].sudo().create(lead_vals)
        self.lead_id = lead
        return lead
