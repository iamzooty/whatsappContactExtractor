import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Documents
from .views import extract_contacts_from_html


class WhatsAppExtractorTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WhatsApp Group Contacts")

    def test_extract_page_loads(self):
        response = self.client.get(reverse("extract"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Extract Contacts")

    def test_sender_page_loads(self):
        response = self.client.get(reverse("sender"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WhatsApp Bulk Sender")

    def test_contact_extractor_normalization(self):
        # Sample HTML with +234, local 080..., and international numbers
        sample_html = """
        <html>
            <body>
                <span class="selectable-text copyable-text" title="+2348031234567, 09012345678, +15551234567, Alice, Bob, You">
                    Group Contacts
                </span>
            </body>
        </html>
        """
        # Test all countries
        contacts_all = extract_contacts_from_html(sample_html, country_filter="all")
        # Should detect: 8031234567 (+234), 9012345678 (+234), 5551234567 (+1)
        phones = [c[0] for c in contacts_all]
        self.assertIn("8031234567", phones)
        self.assertIn("9012345678", phones)
        self.assertIn("5551234567", phones)
        self.assertEqual(len(contacts_all), 3)

        # Test Nigeria only filter
        contacts_ng = extract_contacts_from_html(sample_html, country_filter="234")
        phones_ng = [c[0] for c in contacts_ng]
        self.assertIn("8031234567", phones_ng)
        self.assertIn("9012345678", phones_ng)
        self.assertNotIn("5551234567", phones_ng)
        self.assertEqual(len(contacts_ng), 2)

    def test_extract_post_and_download_flow(self):
        html_data = b"""
        <!DOCTYPE html>
        <html>
            <body>
                <span class="selectable-text copyable-text" title="+234 812 345 6789, +234 701 234 5678, You">
                    Members
                </span>
            </body>
        </html>
        """
        uploaded_file = SimpleUploadedFile(
            "group_sample.html",
            html_data,
            content_type="text/html",
        )

        response = self.client.post(
            reverse("extract"),
            {
                "documents": uploaded_file,
                "contact_prefix": "TestLead",
                "country_filter": "all",
            },
            follow=True,
        )

        # Should redirect to success page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Extraction Successful")
        self.assertContains(response, "TestLead1")

        # Test downloading the file
        doc = Documents.objects.latest("id")
        download_response = self.client.get(reverse("download", args=[doc.id]))
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response["Content-Type"], "text/csv")
        self.assertIn("attachment", download_response["Content-Disposition"])
