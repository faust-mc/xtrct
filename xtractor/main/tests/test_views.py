# main/tests/test_views.py
import os
import json
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from main import views
from main.models import (
    FormName,
    ComponentType,
    FormObject,
    HeaderObjects,
    RowObjects,
    Extraction,
    ExtractedFields,
    ExtractedTable,
)


class TestViews(TestCase):
    def setUp(self):
        # Create a user and login
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="testpass123")
        self.client.login(username="tester", password="testpass123")

        # Basic ComponentType fixtures used by submit_form_ajax/edit_form_ajax
        ComponentType.objects.create(type="Field")
        ComponentType.objects.create(type="Table")

    def test_compute_ocr_reliability_empty(self):
        # No words -> returns 0 score and expected breakdown structure
        ocr_json = {"metadata": {"width": 100, "height": 100}, "readResult": {"blocks": []}}
        res = views.compute_ocr_reliability(ocr_json)
        self.assertEqual(res["score"], 0)
        bd = res["breakdown"]
        self.assertEqual(bd["num_words"], 0)
        self.assertEqual(bd["average_conf"], 0)

    def test_compute_ocr_reliability_basic(self):
        ocr_json = {
            "metadata": {"width": 10, "height": 10},
            "readResult": {
                "blocks": [
                    {
                        "lines": [
                            {"words": [{"text": "Hello", "confidence": 0.9}]},
                            {"words": [{"text": "World", "confidence": 0.8}]},
                        ]
                    }
                ]
            },
        }
        res = views.compute_ocr_reliability(ocr_json)
        self.assertGreater(res["score"], 0)
        self.assertEqual(res["breakdown"]["num_words"], 2)

    def test_get_center_and_is_same_column(self):
        bbox_header = [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}, {"x": 0, "y": 10}]
        bbox_cell = [{"x": 5, "y": 1}, {"x": 15, "y": 1}, {"x": 15, "y": 9}, {"x": 5, "y": 9}]
        center = views.get_center(bbox_header)
        self.assertIsInstance(center, tuple)
        same = views.is_same_column(bbox_header, bbox_cell)
        self.assertTrue(same)

    def test_load_template_list_filters_and_pagination(self):
        # Create some FormName records
        for i in range(15):
            FormName.objects.create(name=f"Form {i}", status=1)

        url = reverse("main:load_template_list")
        # ask for start=0 length=5
        response = self.client.post(url, data={"draw": 1, "start": 0, "length": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recordsTotal", data)
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 5)

        # Test search filter
        response2 = self.client.post(url, data={"draw": 1, "start": 0, "length": 50, "search[value]": "Form 1"})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        # at least matches Form 1, Form 10, Form 11, etc.
        self.assertGreaterEqual(data2["recordsFiltered"], 1)

    def test_submit_form_ajax_missing_method_and_empty(self):
        url = reverse("main:submit_form_ajax")
        # GET is invalid
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

        # POST but missing fields and tables -> should return 400
        resp2 = self.client.post(url, data={})
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("error", resp2.json())

    def test_submit_form_ajax_creates_field_and_table(self):
        url = reverse("main:submit_form_ajax")
        # Prepare POST data: one field and one table (with headers/labels)
        post_data = {
            "form_title": "My Test Form",
            "field_list[]": ["Field A", "Field B"],
            # table_form[0][table_title], headers, labels
            "table_form[0][table_title]": "T1",
            "table_form[0][header][label]": "Row Label",
            "table_form[0][header][label][]": ["R1", "R2"],
            "table_form[0][header]": ["H1", "H2"],
        }

        resp = self.client.post(url, data=post_data)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"))
        # Confirm FormName and FormObjects created
        fn = FormName.objects.get(name="My Test Form")
        self.assertIsNotNone(fn)
        self.assertTrue(FormObject.objects.filter(form_name=fn).exists())

    def test_edit_form_ajax_and_disable(self):
        # Create an original form
        form = FormName.objects.create(name="EditMe", status=1)
        # attach some old FormObject to ensure deletion occurs
        ft = ComponentType.objects.get(type="Field")
        FormObject.objects.create(form_name=form, type=ft, title="Old")

        url = reverse("main:edit_form_ajax", kwargs={"pk": form.pk})
        post_data = {
            "form_title": "Edited Title",
            "field_list[]": ["New Field"],
            "table_form[0][table_title]": "T2",
            "table_form[0][header][label]": "LabelHdr",
            "table_form[0][header][label][]": ["rowA"],
            "table_form[0][header]": ["ColA"],
        }
        resp = self.client.post(url, data=post_data)
        self.assertEqual(resp.status_code, 200)
        j = resp.json()
        self.assertTrue(j.get("success"))
        form.refresh_from_db()
        self.assertEqual(form.name, "Edited Title")
        # disable endpoint
        durl = reverse("main:disable_form_ajax", kwargs={"pk": form.pk})
        dresp = self.client.post(durl)
        self.assertEqual(dresp.status_code, 200)
        dj = dresp.json()
        self.assertTrue(dj.get("success"))
        form.refresh_from_db()
        self.assertEqual(form.status, 0)

    @patch("main.views.analyze_image")
    def test_get_ave_and_ocr_result_view(self, mock_analyze):
        # Mock a simple azure-style response with bounding polygons and words
        mock_ocr = {
            "metadata": {"width": 100, "height": 100},
            "readResult": {
                "blocks": [
                    {
                        "lines": [
                            {
                                "text": "NAME John",
                                "boundingPolygon": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 5}, {"x": 0, "y": 5}],
                                "words": [{"text": "NAME", "confidence": 0.95}, {"text": "John", "confidence": 0.9}],
                            }
                        ]
                    }
                ]
            },
        }
        mock_analyze.return_value = mock_ocr

        # get_ave requires a file upload
        url_ave = reverse("main:get_ave")
        f = BytesIO(b"dummy_image_bytes")
        f.name = "img.png"
        resp = self.client.post(url_ave, data={"file": f})
        self.assertEqual(resp.status_code, 200)
        j = resp.json()
        self.assertIn("score", j)
        self.assertIn("breakdown", j)

        # Prepare a template and components needed by ocr_result_view
        form = FormName.objects.create(name="Tmpl1", status=1)
        ct_field = ComponentType.objects.get(type="Field")
        ct_table = ComponentType.objects.get(type="Table")

        # create a field and a table used by the view
        FormObject.objects.create(form_name=form, type=ct_field, title="NAME")
        tobj = FormObject.objects.create(form_name=form, type=ct_table, title="TBL1")
        HeaderObjects.objects.create(form_object=tobj, header_name="LABEL_HDR", header_type="label")
        HeaderObjects.objects.create(form_object=tobj, header_name="ColA", header_type="value")
        RowObjects.objects.create(form_object=tobj, row_name="R1")

        url_ocr = reverse("main:ocr-result")
        f2 = BytesIO(b"dummy_image_bytes2")
        f2.name = "img2.png"
        resp2 = self.client.post(url_ocr, data={"file": f2, "template_id": str(form.pk)})
        self.assertEqual(resp2.status_code, 200)
        j2 = resp2.json()
        # Expect extracted_fields and extracted_table keys
        self.assertIn("extracted_fields", j2)
        self.assertIn("extracted_table", j2)

    def test_save_form_and_download_excel(self):
        url = reverse("main:save_form")
        # Create a template (FormName) to reference
        tmpl = FormName.objects.create(name="ExcelT", status=1)
        payload = {
            "template": tmpl.pk,
            "extracted_fields": {"F1": {"text": "Val1", "confidence": 0.9}},
            "extracted_table": [
                {"Sample Table": [{"Col1": "A", "Col2": "B"}]}
            ],
        }
        resp = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        j = resp.json()
        self.assertTrue(j.get("success"))
        self.assertIn("download_url", j)
        # Try to download the generated excel file
        download_path = j["download_url"].split("/download_excel/")[-1]
        dl_url = reverse("main:download_excel", kwargs={"filename": download_path})
        dl_resp = self.client.get(dl_url)
        self.assertEqual(dl_resp.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", dl_resp["Content-Type"])

    def test_filter_data_pagination_and_format(self):
        # Create several extractions with varying dates and form_names
        fn1 = FormName.objects.create(name="FilterForm", status=1)
        for i in range(8):
            e = Extraction.objects.create(source="test", form_name=fn1, uploaded_by=self.user)
            ExtractedFields.objects.create(extraction=e, fields={"k": f"v{i}"})
            ExtractedTable.objects.create(extraction=e, table_name="T", data=[{"a": 1}])

        url = reverse("main:filter_data")
        resp = self.client.get(url, data={"form_name": "FilterForm", "page": 1, "per_page": 3})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIn("pagination", data)
        self.assertEqual(data["pagination"]["page"], 1)
        self.assertTrue(data["pagination"]["total_pages"] >= 3)
