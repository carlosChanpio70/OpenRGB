from openrgb import OpenRGBClient
import time
from addons.color import Color
from addons.devices import Devices
from addons.volume import VolumeMonitor 

class NoDevicesFoundError(RuntimeError):
    """Raised when the OpenRGBClient reports no hardware devices."""
    pass

color_2_percentage = 0.2
gradient_min_steps = 4
gradient_max_steps = 6
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]
    
layer_names = Devices().get_layer_names()
purple = Color()
purple.set_hex("#5200b0")
white = Color()
white.set_hsl(0, 0, 100)
colors = [purple, white]

def startup():
    """
    Starts the OpenRGB Client
    :return: The client
    """
    while True:
        try:
            client = OpenRGBClient()
            
            devices = Devices()
            if not client.devices:                          # empty list is falsy
                # no hardware detected yet; raise a specific exception so
                # the outer loop can retry without swallowing unrelated
                # errors
                raise NoDevicesFoundError("no devices found")
            else:
                for device in client.devices:
                    device.set_mode(0)
                    color1 = colors[0].get_color()
                    color2 = colors[1].get_color()

                    devices.add_device(device, color1, color2, color_2_percentage)
                    if device.name == names[1]:
                        devices.set_color_correction(device,zone_name="JRAINBOW2",hue_correction=-20.0)
                    else:
                        devices.set_color_correction(device,zone_index=0,hue_correction=-20.0)
                return client,devices
        except Exception as e:
            print(e)
            time.sleep(.1)

def update_effects(device, devices) -> None:
    devices.set_gradient(device, gradient_min_steps, gradient_max_steps)

    if device.name == names[1]:
        devices.set_color_final(device, colors[0].get_color(hue_correction=-15.0), 0)
    if device.name == names[0]:
        devices.set_volume(device,volume.get_volume())
    devices.apply_final_layer(device)

def main():
    client,devices=startup()

    fps = 24
    frame_time = 1/fps
    
    try:
        while True:
            start = time.time()

            for device in devices.get_device():
                update_effects(device, devices)
            client.show()

            elapsed = time.time() - start
            sleep_time = frame_time - elapsed
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except Exception as e:
        print(e)
        main()

if __name__ == "__main__":
    volume = VolumeMonitor()
    volume.start()
    main()