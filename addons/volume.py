import time
import threading
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
import comtypes


class VolumeMonitor:
    """Threaded audio peak meter monitor."""

    def __init__(self, poll_interval: float = 1 / 60):
        self._volume = 0.0
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._poll_interval = poll_interval

    def get_volume(self) -> float:
        """Return the last sampled peak volume in range [0.0, 1.0]."""
        with self._lock:
            return self._volume

    def start(self) -> None:
        """Start the background audio monitor thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._update_volume_loop,
            name="VolumeMonitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Stop the monitor and wait for the thread to shut down."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _update_volume_loop(self) -> None:
        comtypes.CoInitialize()
        try:
            speakers = AudioUtilities.GetSpeakers()
            if not speakers:
                print("Volume monitor: no speaker device found")
                return

            dev = getattr(speakers, '_dev', None)
            if dev is None:
                print("Volume monitor init: no underlying device")
                return

            interface = dev.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            meter = interface.QueryInterface(IAudioMeterInformation)

            while self._running:
                try:
                    peak = float(meter.GetPeakValue())
                    with self._lock:
                        self._volume = max(0.0, min(1.0, peak))
                except Exception:
                    with self._lock:
                        self._volume = 0.0
                time.sleep(self._poll_interval)

        except Exception as exc:
            print(f"Volume monitor initialization failed: {exc}")
        finally:
            comtypes.CoUninitialize()

if __name__ == "__main__":
    # Test the class directly
    monitor = VolumeMonitor()
    monitor.start()

    try:
        print("Volume monitor class test started. Press Ctrl+C to stop.")
        while True:
            vol = monitor.get_volume()
            print(f"Peak volume: {vol:.4f}", end="\r")
            time.sleep(0.08)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        monitor.stop()