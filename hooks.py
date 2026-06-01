def post_init_hook(env):
    env['website.menu']._union_energy_calculator_ensure_menu()
    env['website.page']._union_energy_calculator_apply_website_config()
