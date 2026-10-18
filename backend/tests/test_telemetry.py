import os
import unittest
from unittest import mock

import telemetry
from telemetry import FLUSH_TIMEOUT_MILLIS, build_instance_id, flush_telemetry


class BuildInstanceIdTest(unittest.TestCase):
    def test_uses_k_revision(self):
        with mock.patch.dict(os.environ, {"K_REVISION": "backend-gemini-00042-abc"}):
            self.assertRegex(build_instance_id(), r"^backend-gemini-00042-abc-[0-9a-f]{8}$")

    def test_fallback_local(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertRegex(build_instance_id(), r"^local-[0-9a-f]{8}$")

    def test_unique(self):
        self.assertNotEqual(build_instance_id(), build_instance_id())

    def test_flush_telemetry_uses_bounded_timeout(self):
        fake_meter = mock.Mock()
        fake_tracer = mock.Mock()
        with mock.patch.object(telemetry, "provider", fake_meter), mock.patch.object(
            telemetry, "tracer_provider", fake_tracer
        ):
            flush_telemetry()
        fake_meter.force_flush.assert_called_once_with(timeout_millis=FLUSH_TIMEOUT_MILLIS)
        fake_meter.shutdown.assert_called_once_with()
        fake_tracer.force_flush.assert_called_once_with(timeout_millis=FLUSH_TIMEOUT_MILLIS)
        fake_tracer.shutdown.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
