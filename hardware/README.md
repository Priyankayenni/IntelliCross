# Hardware deployment notes

IntelliCross runs entirely in software today (`MockSignalController` +
`MockTrafficSimulator`). This document is the path to a physical demo:
a Raspberry Pi driving a real (or model) intersection.

## Two integration levels

**Level 1 — model intersection rig.** Build a small physical
intersection with LEDs (or relay-driven 12V signal heads) on a
breadboard or protoboard. `RaspberryPiSignalController` in
`backend/app/signal_control/gpio_controller.py` drives this directly.

**Level 2 — real traffic cabinet.** Commercial preemption systems
(Opticom, etc.) don't reprogram the controller's logic — they close a
dry contact on a "priority input" that the cabinet's own firmware
already knows how to honor. If you get access to a real or lab
traffic-signal controller, replace the GPIO-direct-drive calls with
relay closures wired to that priority input instead of the light
outputs directly. The `SignalController` interface doesn't change —
only what's behind `set_phase()`.

## Wiring (Level 1 reference build)

| Signal      | Raspberry Pi GPIO (BCM) | Notes                        |
|-------------|--------------------------|-------------------------------|
| NS green    | GPIO 17                  | via relay or transistor driver |
| EW green    | GPIO 27                  | via relay or transistor driver |
| All-red     | GPIO 22                  | drives both red channels       |

Use a relay module or NPN transistor + flyback diode between the GPIO
pin and any load above the Pi's 3.3V/16mA-per-pin limit — never wire
LEDs or relays directly to a GPIO pin without a current-limiting
resistor or driver stage.

## Bringing it up

```bash
# on the Pi
pip install RPi.GPIO --break-system-packages
```

Then in `backend/app/core/pipeline.py`, swap:

```python
self.controller = MockSignalController()
```

for:

```python
from app.signal_control.gpio_controller import RaspberryPiSignalController
self.controller = RaspberryPiSignalController()
```

Everything else — the preemption engine, the detector, the API, the
dashboard — is unchanged, because they only ever talk to the
`SignalController` interface.

## Real camera input

Once you're ready to detect real emergency vehicles instead of
simulated ones, point `VehicleDetector` (see
`backend/app/detection/detector.py`) at frames from:
- a USB webcam (`cv2.VideoCapture(0)`), or
- an RTSP/IP camera stream, or
- recorded footage for offline evaluation.

The heuristic emergency-vehicle classifier in that file is a
placeholder — for a real result you'll want to fine-tune YOLOv8n on an
emergency-vehicle dataset (several open ones exist on Roboflow
Universe) and point `DetectorConfig.weights` at the resulting
checkpoint.
