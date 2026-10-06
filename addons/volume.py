import time
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
import comtypes


class VolumeMonitor:
    """Audio peak meter sampled by the caller."""

    def __init__(self):
        self._volume = 0.0
        self._meter = None
        self._com_initialized = False

    def get_volume(self) -> float:
        """Return the last sampled peak volume in range [0.0, 1.0]."""
        return self._volume

    def start(self) -> None:
        """Initialize the audio meter on the thread that will sample it."""
        if self._meter is not None:
            return

        comtypes.CoInitialize()
        self._com_initialized = True
        try:
            speakers = AudioUtilities.GetSpeakers()
            if not speakers:
                print("Volume monitor: no speaker device found")
                self.stop()
                return

            dev = getattr(speakers, "_dev", None)
            if dev is None:
                print("Volume monitor init: no underlying device")
                self.stop()
                return

            interface = dev.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            self._meter = interface.QueryInterface(IAudioMeterInformation)
        except Exception as exc:
            print(f"Volume monitor initialization failed: {exc}")
            self.stop()

    def update_volume(self) -> None:
        """Sample the peak volume once; call from the main loop."""
        if self._meter is None:
            return

        try:
            peak = float(self._meter.GetPeakValue())
            self._volume = max(0.0, min(1.0, peak))
        except Exception:
            self._volume = 0.0

    def stop(self) -> None:
        """Release the meter and uninitialize COM on the calling thread."""
        self._meter = None
        if self._com_initialized:
            comtypes.CoUninitialize()
            self._com_initialized = False


if __name__ == "__main__":
    # Test the class directly
    monitor = VolumeMonitor()
    monitor.start()

    try:
        print("Volume monitor class test started. Press Ctrl+C to stop.")
        while True:
            monitor.update_volume()
            vol = monitor.get_volume()
            print(f"Peak volume: {vol:.4f}", end="\r")
            time.sleep(1 / 60)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        monitor.stop()