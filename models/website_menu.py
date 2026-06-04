from odoo import api, models

CALCULATOR_MENU_URL = '/solar-savings-calculator'
CALCULATOR_MENU_NAME = 'Calculator'
CALCULATOR_MENU_SEQUENCE = 20


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    @api.model
    def _union_energy_calculator_ensure_menu(self):
        """One Calculator entry as direct child of the site top menu."""
        Menu = self.sudo()
        for website in self.env['website'].search([]):
            top_menu = self._union_energy_web_get_site_top_menu(website)
            if not top_menu:
                continue

            matches = Menu.search([
                '|',
                ('url', '=', CALCULATOR_MENU_URL),
                '&',
                ('name', '=', CALCULATOR_MENU_NAME),
                ('website_id', 'in', (False, website.id)),
            ], order='id')
            matches = matches.filtered(lambda m: m.id != top_menu.id)

            under_top = matches.filtered(lambda m: m.parent_id == top_menu)
            if under_top:
                keep = under_top[0]
            elif matches:
                keep = matches[0]
            else:
                keep = Menu.create({
                    'name': CALCULATOR_MENU_NAME,
                    'url': CALCULATOR_MENU_URL,
                    'parent_id': top_menu.id,
                    'website_id': website.id,
                    'sequence': CALCULATOR_MENU_SEQUENCE,
                })

            if keep.child_id:
                keep.child_id.write({'parent_id': top_menu.id})

            self._union_energy_web_safe_unlink_menus(matches - keep)
            self._union_energy_web_write_nav_item(
                keep, top_menu, website, CALCULATOR_MENU_NAME, CALCULATOR_MENU_URL, CALCULATOR_MENU_SEQUENCE,
            )
