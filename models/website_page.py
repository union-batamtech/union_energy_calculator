from odoo import api, models


class WebsitePage(models.Model):
    _inherit = 'website.page'

    @api.model
    def _union_energy_calculator_apply_website_config(self):
        """Unpublish CMS page; controller serves /solar-savings-calculator."""
        page = self.env.ref(
            'union_energy_web.page_solar_savings_calculator',
            raise_if_not_found=False,
        )
        if page:
            page.is_published = False
