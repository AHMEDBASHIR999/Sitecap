import json
from django.test import TestCase, Client
from django.urls import reverse

class AhmedTestVibrationSyncTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ahmedtest_page_renders(self):
        response = self.client.get('/ahmedtest/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AhmedTest')
        self.assertContains(response, 'Tap-Tap Vibration Pad')
        self.assertContains(response, 'attachHapticTrigger')

    def test_device_pairing_and_vibration_sync(self):
        # 1. Device 1 joins room 123
        resp1 = self.client.post(
            '/api/ahmedtest/join/',
            data=json.dumps({'code': '123', 'device_id': 'iphone_ahmed', 'device_name': 'iPhone 15'}),
            content_type='application/json'
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertTrue(data1['success'])
        self.assertEqual(data1['role'], 'Device 1')
        self.assertFalse(data1['connected']) # Only 1 device so far

        # 2. Device 2 joins room 123
        resp2 = self.client.post(
            '/api/ahmedtest/join/',
            data=json.dumps({'code': '123', 'device_id': 'android_partner', 'device_name': 'Samsung Galaxy'}),
            content_type='application/json'
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertTrue(data2['success'])
        self.assertEqual(data2['role'], 'Device 2')
        self.assertTrue(data2['connected']) # Both devices connected!

        # 3. Device 1 sends Heartbeat vibration
        send_resp = self.client.post(
            '/api/ahmedtest/send/',
            data=json.dumps({
                'code': '123',
                'device_id': 'iphone_ahmed',
                'style': 'heartbeat',
                'pattern': [120, 160, 120, 600, 120]
            }),
            content_type='application/json'
        )
        self.assertEqual(send_resp.status_code, 200)
        send_data = send_resp.json()
        self.assertTrue(send_data['success'])
        seq_num = send_data['seq']

        # 4. Device 2 polls sync and receives Device 1's vibration
        sync_resp = self.client.get(f'/api/ahmedtest/sync/?code=123&device_id=android_partner&last_seq=0')
        self.assertEqual(sync_resp.status_code, 200)
        sync_data = sync_resp.json()
        self.assertTrue(sync_data['connected'])
        self.assertEqual(len(sync_data['events']), 1)
        self.assertEqual(sync_data['events'][0]['style'], 'heartbeat')
        self.assertEqual(sync_data['events'][0]['sender_id'], 'iphone_ahmed')

        # 5. Device 1 polling shouldn't receive its own event
        sync_resp1 = self.client.get(f'/api/ahmedtest/sync/?code=123&device_id=iphone_ahmed&last_seq=0')
        sync_data1 = sync_resp1.json()
        self.assertEqual(len(sync_data1['events']), 0)

        # 6. Device 1 leaves room
        leave_resp = self.client.post(
            '/api/ahmedtest/leave/',
            data=json.dumps({'code': '123', 'device_id': 'iphone_ahmed'}),
            content_type='application/json'
        )
        self.assertEqual(leave_resp.status_code, 200)

