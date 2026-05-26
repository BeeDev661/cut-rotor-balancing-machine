import asyncio
import json
import time
import numpy as np


class Simulator:
    def __init__(self):
        self.running = False
        self.rpm = 600.0
        self.sample_rate = 2048  # Hz
        self.amp = 1.0
        self.noise_std = 0.05

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def set_speed(self, rpm: float):
        self.rpm = float(rpm)

    async def stream_chunk(self, duration: float = 0.1):
        n = int(self.sample_rate * duration)
        t = np.arange(n) / self.sample_rate
        rotor_hz = max(0.1, self.rpm / 60.0)
        # simple imbalance signal at rotor frequency and its harmonics
        signal = (
            self.amp * np.sin(2 * np.pi * rotor_hz * t)
            + 0.3 * self.amp * np.sin(2 * np.pi * 2 * rotor_hz * t)
        )
        noise = np.random.normal(scale=self.noise_std, size=n)
        acc = (signal + noise).astype(float)
        msg = {
            "timestamp": time.time(),
            "rpm": float(self.rpm),
            "sample_rate": int(self.sample_rate),
            "acc": acc.tolist(),
        }
        await asyncio.sleep(duration)
        return json.dumps(msg)
