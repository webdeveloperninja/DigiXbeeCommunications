import unittest
import sys
from unittest.mock import MagicMock

sys.path.insert(0, '../')

mock_umqtt = MagicMock()

sys.modules['umqtt.simple'] = mock_umqtt
sys.modules['machine'] = MagicMock()

from connection import AzureMQTT


class TestAzureMQTT(unittest.TestCase):
    def test_should_initialize_client(self):
        device_id = 'test-device'
        shared_access_key = 'iIoaaLKcwWOl/LdbVJYeff2E452hCYJkmrWK3MQVjzI='
        host_name = 'iot.azure-devices.net'
        azure_iot_hub_connection_string = f'HostName={host_name};DeviceId={device_id};SharedAccessKey={shared_access_key}'

        connection = AzureMQTT(azure_iot_hub_connection_string)

        self.assertIsNotNone(connection)


if __name__ == '__main__':
    unittest.main()
