from odoo import api, models

CALCULATOR_MENU_URL = '/solar-savings-calculator'
CALCULATOR_MENU_NAME = 'Solar Savings Calculator'
CALCULATOR_MENU_SEQUENCE = 16


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    @api.model
    def _union_energy_calculator_ensure_menu(self):
        """Ensure calculator menu lives under each website top menu (visible in navbar)."""
        default_main = self.env.ref('website.main_menu', raise_if_not_found=False)
        if not default_main:
            return

        for website in self.env['website'].search([]):
            top_menu = website.menu_id
            if not top_menu:
                continue

            all_menus = self.search([('url', '=', CALCULATOR_MENU_URL)])
            under_top = all_menus.filtered(lambda m: m.parent_id == top_menu)
            under_default = all_menus.filtered(
                lambda m: m.parent_id == default_main
            )
            stray = all_menus - under_top - under_default

            if under_top:
                under_top[:1].write({
                    'name': CALCULATOR_MENU_NAME,
                    'website_id': website.id,
                    'sequence': CALCULATOR_MENU_SEQUENCE,
                    'page_id': False,
                })
                (under_top[1:] | under_default | stray).unlink()
                continue

            if under_default:
                under_default[:1].write({
                    'name': CALCULATOR_MENU_NAME,
                    'parent_id': top_menu.id,
                    'website_id': website.id,
                    'sequence': CALCULATOR_MENU_SEQUENCE,
                    'page_id': False,
                })
                (under_default[1:] | stray).unlink()
                continue

            stray.unlink()
            self.create({
                'name': CALCULATOR_MENU_NAME,
                'url': CALCULATOR_MENU_URL,
                'parent_id': top_menu.id,
                'website_id': website.id,
                'sequence': CALCULATOR_MENU_SEQUENCE,
                'page_id': False,
            })
