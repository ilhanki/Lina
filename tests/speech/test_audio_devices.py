from lina.speech.audio_devices import AudioInputDeviceService


class Default:
    device = (1, 4)


class FakeBackend:
    default = Default()

    def __init__(self):
        self.devices = [
            {"name": "Output", "max_input_channels": 0},
            {"name": "Default Mic", "max_input_channels": 2},
            {"name": "USB Mic", "max_input_channels": 1},
        ]

    def query_devices(self, device=None, kind=None):
        if device is not None:
            return self.devices[device]
        if kind == "input":
            return self.devices[1]
        return self.devices


def test_lists_only_input_devices_and_marks_default():
    devices = AudioInputDeviceService(FakeBackend()).list_devices()
    assert [device.name for device in devices] == ["Default Mic", "USB Mic"]
    assert devices[0].is_default


def test_selected_and_default_device_resolution():
    service = AudioInputDeviceService(FakeBackend())
    assert service.resolve(2) == 2
    assert service.resolve(None) == 1


def test_missing_device_falls_back_to_default(caplog):
    service = AudioInputDeviceService(FakeBackend())
    assert service.resolve(99) == 1
    assert "audio_input_fallback" in caplog.text


def test_device_test_and_unavailable_backend():
    service = AudioInputDeviceService(FakeBackend())
    assert service.test_device(2)

    class Broken:
        def query_devices(self, *args, **kwargs):
            raise RuntimeError("private")

    broken = AudioInputDeviceService(Broken())
    assert broken.list_devices() == ()
    assert not broken.is_available()
    assert not broken.test_device()
