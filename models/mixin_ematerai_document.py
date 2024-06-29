from odoo import api, fields, models


class MixinEmateraiDocument(models.AbstractModel):
    _inherit = "mixin.ematerai_document"

    @api.depends("ematerai_document_ids", "ematerai_document_ids.state")
    def _compute_ematerai_total(self):
        for document in self:
            result = 0
            ematerai_success = document.ematerai_document_ids.filtered(
                lambda x: x.state == "completed"
            )
            if ematerai_success:
                result = len(ematerai_success)
            document.ematerai_total = result
