from odoo import fields, models


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
