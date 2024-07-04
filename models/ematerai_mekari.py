import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import hmac
import base64
import hashlib
import datetime
import requests
import PyPDF2
from io import BytesIO


class EmateraiMekari(models.Model):
    _name = "ematerai.mekari"
    _inherits = {"ematerai.document": "ematerai_document_id"}
    _description = "E-Materai Document for Mekari"

    ematerai_document_id = fields.Many2one(
        string="E-Materai Document",
        comodel_name="ematerai.document",
        required=True,
        ondelete="cascade",
    )
    mekari_document_id = fields.Char(
        string="Document ID",
    )

    def _action_submit_ematerai(self):
        self.ensure_one()
        response = False
        if not self.mekari_document_id:
            path = self._get_mekari_stamp_api()
            request_body = self._prepare_param_data()
            try:
                # Include HMAC authentication in the request
                response = self._mekari_api_request_with_hmac("POST", path, request_body)
            except requests.exceptions.Timeout:
                raise UserError("Timeout: the server did not reply within 30s")
            err_resp = self._parse_error_response(response)
            if response.status_code == 200:
                data = self.get_mekari_data(response)
                if "id" in data:
                    self.mekari_document_id = data["id"]
                    self.write(self._prepare_submit_document_data())
                    self._message_submit_ematerai()
            else:
                msg_err = _(err_resp)
                raise UserError(msg_err)
        return response

    def _action_check_ematerai(self):
        self.ensure_one()
        if self.mekari_document_id:
            path = self._get_mekari_check_document() + self.mekari_document_id
            try:
                response = self._mekari_api_request_with_hmac("GET", path)
            except requests.exceptions.Timeout:
                raise UserError("Timeout: the server did not reply within 30s")
            err_resp = self._parse_error_response(response)
            if response.status_code == 200:
                stamp_status = self.get_mekari_data(response, "status")
                self.write(self._prepare_check_document_data(stamp_status))
            else:
                msg_err = _(err_resp)
                raise UserError(msg_err)
        else:
            raise UserError("Document ID not found")

    def _action_generate_ematerai(self):
        self.ensure_one()
        if self.state == 'm_success':
            path = self._get_mekari_download_document().format(document_id=self.mekari_document_id)
            try:
                response = self._mekari_api_request_with_hmac("GET", path)
            except requests.exceptions.Timeout:
                raise UserError("Timeout: the server did not reply within 30s")
            err_resp = self._parse_error_response(response)
            if response.status_code == 200:
                self.write(self._prepare_download_document_data(response.content))
                self._post_ematerai()
            else:
                msg_err = _(err_resp)
                raise UserError(msg_err)
        else:
            raise UserError("Cannot generate E-Materai file")

    def _prepare_param_data(self):
        # Decode the original attachment data
        decoded_data = base64.b64decode(self.original_attachment_data)
        encoded_data = base64.b64encode(decoded_data).decode('utf-8')

        # Read the PDF and extract the first page's dimensions
        pdf_file = BytesIO(decoded_data)
        reader = PyPDF2.PdfFileReader(pdf_file)
        page = reader.getPage(0)
        width, height = page.mediaBox.getWidth(), page.mediaBox.getHeight()

        # Prepare the annotation details
        annotation = {
            "page": self.type_id.visual_sign_page,
            "element_width": self.type_id.visual_urx - self.type_id.visual_iix,
            "element_height": self.type_id.visual_ury - self.type_id.visual_iiy,
            "position_x": self.type_id.visual_urx,
            "position_y": self.type_id.visual_ury,
            "canvas_width": width,
            "canvas_height": height,
            "type_of": "meterai"
        }

        # Construct the final parameter dictionary
        param_data = {
            "doc": encoded_data,
            "filename": self.original_datas_fname,
            "annotations": [annotation],
        }

        return param_data

    def _mekari_api_request_with_hmac(self, method_api, path_api, body_api=None):
        client_id = self._get_client_id()
        client_secret = self._get_client_secret()
        base_url = self._get_base_url()

        method = method_api
        datetime_now = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        # Construct the payload for HMAC signature generation
        request_line = f"{method} {path_api} HTTP/1.1"
        payload = f"date: {datetime_now}\n{request_line}"

        secret = client_secret.encode()
        digest = hmac.new(secret, payload.encode(), hashlib.sha256)
        signature = base64.b64encode(digest.digest()).decode()

        # Create the authorization header with HMAC details
        headers = {
            'Content-Type': 'application/json',
            'Date': datetime_now,
            'Authorization': (
                f'hmac username="{client_id}", algorithm="hmac-sha256", '
                f'headers="date request-line", signature="{signature}"'
            )
        }

        request_url = base_url + path_api
        response = requests.request(method, request_url, headers=headers, json=body_api)
        return response

    @api.multi
    def _get_credentials_param(self, param):
        self.ensure_one()
        obj_ir_config_parameter = self.env["ir.config_parameter"].sudo()
        result = obj_ir_config_parameter.get_param(
            param,
            default=False,
        )
        return result

    @api.multi
    def _get_client_id(self):
        self.ensure_one()
        client_id = self._get_credentials_param("mekari_config.mkr_client_id")
        if not client_id:
            msg_err = _("Client ID Not Found")
            raise UserError(msg_err)
        return client_id

    @api.multi
    def _get_client_secret(self):
        self.ensure_one()
        client_secret = self._get_credentials_param("mekari_config.mkr_client_secret")
        if not client_secret:
            msg_err = _("Client Secret Not Found")
            raise UserError(msg_err)
        return client_secret

    @api.multi
    def _get_mekari_stamp_api(self):
        self.ensure_one()
        mekari_stamp_api = self._get_credentials_param("mekari_config.mkr_stamp_api")
        if not mekari_stamp_api:
            msg_err = _("Mekari Stamp API Not Found")
            raise UserError(msg_err)
        return mekari_stamp_api

    @api.multi
    def _get_mekari_check_document(self):
        self.ensure_one()
        mekari_check_stamp_api = self._get_credentials_param("mekari_config.mkr_check_stamp_api")
        if not mekari_check_stamp_api:
            msg_err = _("Mekari Check Stamp API Not Found")
            raise UserError(msg_err)
        return mekari_check_stamp_api

    @api.multi
    def _get_mekari_download_document(self):
        self.ensure_one()
        mekari_download_stamp_api = self._get_credentials_param("mekari_config.mkr_download_stamp_api")
        if not mekari_download_stamp_api:
            msg_err = _("Mekari Download Stamp API Not Found")
            raise UserError(msg_err)
        return mekari_download_stamp_api

    @api.multi
    def _get_base_url(self):
        self.ensure_one()
        base_url = self._get_credentials_param("mekari_config.mkr_base_url")
        if not base_url:
            msg_err = _("Base URL Not Found")
            raise UserError(msg_err)
        return base_url

    def _parse_error_response(self, response):
        """Parse the error response and return a formatted error message."""
        try:
            error_data = response.json().get('data', {})
            message = error_data.get('message', response.text)
            params = error_data.get('params', {})
            try:
                message_conv = json.loads(message)
                detailed_message = message_conv.get('message', message)
            except json.JSONDecodeError:
                detailed_message = message
            for param, errors in params.items():
                detailed_message += f"\n{param}: " + "; ".join(errors)
            return detailed_message
        except Exception as e:
            return f"Failed to parse error response: {str(e)}"

    @api.multi
    def get_mekari_data(self, data, type=False):
        result = {}
        data_json = data.json()
        if "data" in data_json:
            result = data_json["data"]
        if type == 'status':
            result = data_json["data"]["attributes"]["stamping_status"]
        return result

    @api.multi
    def _prepare_submit_document_data(self):
        return {"state": "submitted"}

    @api.multi
    def _prepare_check_document_data(self, stamp_status):
        status_map = {
            'none': "m_none",
            'in_progress': "m_in_progress",
            'pending': "m_pending",
            'failed': "m_failed",
            'success': "m_success"
        }
        return {"state": status_map.get(stamp_status)}

    @api.multi
    def _prepare_download_document_data(self, data):
        self.ensure_one()
        attachment_id = self._get_document(data)
        return {"ematerai_attachment_id": attachment_id, "state": "completed"}

    @api.multi
    def _get_document(self, data):
        self.ensure_one()
        obj_ir_attachment = self.env["ir.attachment"]
        b64_pdf = base64.b64encode(data)
        datetime_now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = "ematerai_" + datetime_now
        ir_values = {
            "name": filename,
            "type": "binary",
            "datas": b64_pdf,
            "datas_fname": filename + ".pdf",
            "store_fname": filename,
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/x-pdf",
        }
        attachment_id = obj_ir_attachment.create(ir_values)
        return attachment_id.id

    @api.multi
    def _message_submit_ematerai(self):
        self.ensure_one()
        criteria = [("id", "=", self.res_id)]
        document = self.env[self.model].search(criteria)
        message = ("Meterai processing. Please wait a few moments. "
                   "Check status via the 'Check E-meterai' button in "
                   "the list or contact Mekari support if not issued within 15 minutes")
        document.message_post(body=message, message_type="notification")

    @api.multi
    def _post_ematerai(self):
        self.ensure_one()
        criteria = [("id", "=", self.res_id)]
        document = self.env[self.model].search(criteria)
        message = _("E-Materai is successfully created")
        _attachments = [
            (
                self.ematerai_attachment_id.datas_fname,
                base64.b64decode(self.ematerai_attachment_data),
            ),
        ]
        document.message_post(
            body=message, message_type="notification", attachments=_attachments
        )

    @api.multi
    def action_submit_ematerai(self):
        self._action_submit_ematerai()

    @api.multi
    def action_check_ematerai(self):
        self._action_check_ematerai()
