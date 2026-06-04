from odoo import api, models


class WebsitePage(models.Model):
    _inherit = 'website.page'

    @api.model
    def _union_energy_calculator_apply_website_config(self):
        """Route is served by controller; unpublish any leftover CMS page."""
        pages = self.env['website.page'].sudo().search([
            ('url', '=', '/solar-savings-calculator'),
        ])
        if pages:
            pages.write({'is_published': False})
