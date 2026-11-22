import json
from django.test import TestCase, Client
from API.ebay_research import parse_links_input, title_tokens, parse_realistic_price


class EbayResearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ebay_research_page_loads(self):
        """Test both /ebay-research/ and /ebayresearch/ URLs load successfully"""
        resp1 = self.client.get('/ebay-research/')
        self.assertEqual(resp1.status_code, 200)
        self.assertContains(resp1, "eBay vs AliExpress Visual Research")
        self.assertContains(resp1, "EBAY_CLIENT_ID")

        resp2 = self.client.get('/ebayresearch/')
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, "EBAY_CLIENT_ID")

    def test_link_parsing_uk(self):
        """Test parsing of UK eBay links and sold counts"""
        text = """
        https://www.ebay.co.uk/itm/123456789012 18 sold
        https://www.ebay.co.uk/itm/987654321098
        """
        items_map, raw_count = parse_links_input(text, country="UK")
        self.assertEqual(raw_count, 2)
        self.assertIn("123456789012", items_map)
        self.assertEqual(items_map["123456789012"]["sold"], 18)
        self.assertEqual(items_map["123456789012"]["country"], "UK")

    def test_link_parsing_auto_detection(self):
        """Test auto-detection of country from link domain"""
        text = """
        https://www.ebay.co.uk/itm/111111111111 (sold 5)
        https://www.ebay.com.au/itm/222222222222
        https://www.ebay.com/itm/333333333333 (12 sold)
        """
        items_map, raw_count = parse_links_input(text, country="AUTO")
        self.assertEqual(raw_count, 3)
        self.assertEqual(items_map["111111111111"]["country"], "UK")
        self.assertEqual(items_map["222222222222"]["country"], "AUS")
        self.assertEqual(items_map["333333333333"]["country"], "USA")

    def test_empty_run_validation(self):
        """Test that running with empty links yields clear validation error"""
        resp = self.client.post(
            '/ebay-research/api/run/',
            data=json.dumps({"links": ""}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["success"])
        self.assertIn("at least one eBay item link", data["message"])

    def test_test_connection_invalid_service(self):
        """Test validation on test connection endpoint"""
        resp = self.client.post(
            '/ebay-research/api/test/',
            data=json.dumps({"service": "invalid_svc"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_export_endpoints(self):
        """Test HTML, CSV, and JSON export endpoints"""
        sample_results = [{
            "id": "123456789012",
            "country": "UK",
            "country_name": "United Kingdom",
            "ts": 1700000000,
            "age": "2.5d",
            "curr": "£",
            "currency_code": "GBP",
            "title": "Vintage Mechanical Watch",
            "price": 45.0,
            "sold": 10,
            "seller": "top_seller_uk",
            "loc": "GB",
            "link": "https://www.ebay.co.uk/itm/123456789012",
            "thumb": "https://i.ebayimg.com/thumb.jpg",
            "large": "https://i.ebayimg.com/large.jpg",
            "spread": 25.0,
            "top3": [{
                "title": "Retro Mechanical Wristwatch",
                "price": 20.0,
                "score": 85.5,
                "url": "https://www.aliexpress.com/item/999.html",
                "img": "https://ali.com/img.jpg",
                "trusted": 1,
                "vol": 120
            }]
        }]
        sample_summary = {
            "total_links": 1,
            "unique_items": 1,
            "loaded_items": 1,
            "matches_70_plus": 1,
            "avg_spread": 25.0,
            "hot_items": 1,
            "elapsed_seconds": 1.2
        }

        # Test HTML export
        resp_html = self.client.post(
            '/ebay-research/api/export/',
            data=json.dumps({"format": "html", "results": sample_results, "summary": sample_summary}),
            content_type="application/json"
        )
        self.assertEqual(resp_html.status_code, 200)
        self.assertEqual(resp_html['Content-Type'], 'text/html; charset=utf-8')
        self.assertIn("Vintage Mechanical Watch", resp_html.content.decode('utf-8'))

        # Test CSV export
        resp_csv = self.client.post(
            '/ebay-research/api/export/',
            data=json.dumps({"format": "csv", "results": sample_results, "summary": sample_summary}),
            content_type="application/json"
        )
        self.assertEqual(resp_csv.status_code, 200)
        self.assertEqual(resp_csv['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn("Vintage Mechanical Watch", resp_csv.content.decode('utf-8'))

        # Test JSON export
        resp_json = self.client.post(
            '/ebay-research/api/export/',
            data=json.dumps({"format": "json", "results": sample_results, "summary": sample_summary}),
            content_type="application/json"
        )
        self.assertEqual(resp_json.status_code, 200)
        self.assertEqual(resp_json['Content-Type'], 'application/json; charset=utf-8')
        data = json.loads(resp_json.content.decode('utf-8'))
        self.assertEqual(len(data["results"]), 1)
