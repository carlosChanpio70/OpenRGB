import time
import threading
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
import comtypes

# Global variable + lock for safe cross-thread access
_volume = 0.0
_volume_lock = threading.Lock()
_running = True
_update_thread = None


def get_volume() -> float:
    """Get the current volume peak level (0.0 to 1.0)"""
    with _volume_lock:
        return _volume


def _update_volume_loop():
    """Background thread that updates volume"""
    comtypes.CoInitialize()
    try:
        # 1. Get the device wrapper
        sessions = AudioUtilities.GetSpeakers()
        if not sessions:
            return

        # 2. Access the underlying COM device and activate the meter
        # the AudioDevice object uses `_dev` (not `_device`) for the IMMDevice
        dev = getattr(sessions, '_dev', None)
        if dev is None:
            # unexpected API change - bail out gracefully
            print("Volume meter init: no underlying device")
            return

        interface = dev.Activate(
            IAudioMeterInformation._iid_,
            CLSCTX_ALL,
            None
        )

        # 3. Cast to the correct interface
        meter = interface.QueryInterface(IAudioMeterInformation)

        while _running:
            try:
                peak = meter.GetPeakValue()
                with _volume_lock:
                    global _volume
                    # Clamp and set
                    _volume = max(0.0, min(1.0, peak))
            except Exception:
                with _volume_lock:
                    _volume = 0.0
            time.sleep(1 / 60)

    except Exception as e:
        print(f"Volume meter initialization failed: {e}")
    finally:
        comtypes.CoUninitialize()


def start_volume_monitor():
    """Start the background volume update thread"""
    global _update_thread, _running

    if _update_thread is not None and _update_thread.is_alive():
        return  # already running

    _running = True
    _update_thread = threading.Thread(
        target=_update_volume_loop,
        name="VolumeMonitor",
        daemon=True          # ← important: auto-closes when main program exits
    )
    _update_thread.start()
    print("Volume monitor started")


def stop_volume_monitor():
    """Request the volume thread to stop"""
    global _running
    _running = False
    if _update_thread is not None:
        _update_thread.join(timeout=2.0)


# ────────────────────────────────────────────────
#           Usage example
# ────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Start monitoring
    start_volume_monitor()

    try:
        while True:
            vol = get_volume()
            print(f"Peak volume: {vol:.4f}", end="\r")
            time.sleep(0.08)  # ~12 fps display

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_volume_monitor()