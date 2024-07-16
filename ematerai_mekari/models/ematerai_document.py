from odoo import _, api, fields, models


class EmateraiDocument(models.Model):
    _inherit = "ematerai.document"

    state = fields.Selection(selection_add=[('m_none', 'None'), ('m_in_progress', 'In Progress Stamp'),
                                            ('m_pending', 'Pending Stamp'), ('m_failed', 'Failed Stamp'),
                                            ('m_success', 'Success Stamp'), ('completed', 'Completed')])

    @api.multi
    def action_submit_ematerai(self):
        for document in self:
            if document.provider_id:
                document.provider_id._action_submit_ematerai()

    @api.multi
    def action_check_ematerai(self):
        for document in self:
            if document.provider_id:
                document.provider_id._action_check_ematerai()
