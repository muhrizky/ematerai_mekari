import base64
import tempfile
from datetime import datetime

import ghostscript

from odoo import api, fields, models


class CreateEmaterai(models.TransientModel):
    _inherit = "create.ematerai"

    @api.multi
    def _prepare_attachment_data(self, report_id):
        self.ensure_one()
        active_ids = self.env.context.get("active_ids", False)
        active_model = self.env.context.get("active_model", "")
        if report_id.report_type == "aeroo":
            pdf = report_id.render_aeroo(active_ids, {})
        else:
            pdf = report_id.render_qweb_pdf(active_ids)

        b64_pdf = base64.b64encode(pdf[0])  # Bytes
        input_pdf = tempfile.NamedTemporaryFile()
        output_pdf = tempfile.NamedTemporaryFile()

        try:
            input_pdf.write(base64.b64decode(b64_pdf))
            args = [
                "downgradePDF",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.6",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-sOutputFile=" + output_pdf.name,
                input_pdf.name,
            ]
            ghostscript.Ghostscript(*args)
            output_pdf.seek(0)
            b64_pdf_new = base64.b64encode(output_pdf.read())
        finally:
            input_pdf.close()
            output_pdf.close()

        datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = "report_" + datetime_now
        # Search for the object using the active model and active IDs
        obj = self.env[active_model].search([('id', 'in', active_ids)], limit=1)
        # Custom filename if the document is an invoice and its state is either 'open' or 'paid'
        if obj.type == 'out_invoice' and obj.state in ('open', 'paid'):
            number = obj.number or ''
            if obj.partner_id.parent_id:
                partner_name = obj.partner_id.parent_id.name
            else:
                partner_name = obj.partner_id.name
            filename = 'Invoice - {} - {}'.format(number.replace('/', '_'), partner_name)

        return {
            "name": filename,
            "type": "binary",
            "datas": b64_pdf_new,
            "datas_fname": filename + ".pdf",
            "store_fname": filename,
            "res_model": active_model,
            "res_id": active_ids[0],
            "mimetype": "application/x-pdf",
        }
