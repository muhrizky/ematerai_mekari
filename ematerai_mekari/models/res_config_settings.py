from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_mekari = fields.Boolean(string="Mekari", default="True")
    mkr_base_url = fields.Char(string="Base URL")
    mkr_client_id = fields.Char(string="Client ID")
    mkr_client_secret = fields.Char(string="Client Secret")
    mkr_stamp_api = fields.Char(string="Stamp API")
    mkr_check_stamp_api = fields.Char(string="Check Stamp API")
    mkr_download_stamp_api = fields.Char(string="Download Stamp API")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        # Get the value from the system parameters
        mekari = self.env['ir.config_parameter'].sudo().get_param('mekari_config.module_mekari', default=False)
        mkr_base_url = self.env['ir.config_parameter'].sudo().get_param('mekari_config.mkr_base_url', default=False)
        mkr_client_id = self.env['ir.config_parameter'].sudo().get_param('mekari_config.mkr_client_id', default=False)
        mkr_client_secret = self.env['ir.config_parameter'].sudo().get_param('mekari_config.mkr_client_secret',
                                                                             default=False)
        mkr_stamp_api = self.env['ir.config_parameter'].sudo().get_param('mekari_config.mkr_stamp_api', default=False)
        mkr_check_stamp_api = self.env['ir.config_parameter'].sudo().get_param('mekari_config.mkr_check_stamp_api', default=False)
        mkr_download_stamp_api = self.env['ir.config_parameter'].sudo().get_param('mekari_config.mkr_download_stamp_api', default=False)
        res.update(
            module_mekari=mekari,
            mkr_base_url=mkr_base_url,
            mkr_client_id=mkr_client_id,
            mkr_client_secret=mkr_client_secret,
            mkr_stamp_api=mkr_stamp_api,
            mkr_check_stamp_api=mkr_check_stamp_api,
            mkr_download_stamp_api=mkr_download_stamp_api,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        # Set the value in the system parameters
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.module_mekari', self.module_mekari)
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.mkr_base_url', self.mkr_base_url)
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.mkr_client_id', self.mkr_client_id)
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.mkr_client_secret', self.mkr_client_secret)
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.mkr_stamp_api', self.mkr_stamp_api)
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.mkr_check_stamp_api', self.mkr_check_stamp_api)
        self.env['ir.config_parameter'].sudo().set_param('mekari_config.mkr_download_stamp_api', self.mkr_download_stamp_api)
