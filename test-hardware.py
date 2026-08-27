#!/usr/bin/env python3
"""Teste contínuo das 10 botoeiras e dos 10 anéis WS2812B.

Sem botão pressionado, um anel azul percorre o painel continuamente. Ao apertar
uma botoeira, o anel correspondente fica verde. CTRL+C encerra e apaga tudo.
"""

from __future__ import annotations

import os
import time


os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

from gpiozero import Button
from pi5neo import Pi5Neo


SPI_DEVICE = os.getenv("SPI_DEVICE", "/dev/spidev0.0")
SPI_SPEED_KHZ = int(os.getenv("SPI_SPEED_KHZ", "800"))
RING_COUNT = int(os.getenv("RING_COUNT", "10"))
LEDS_PER_RING = int(os.getenv("LEDS_PER_RING", "12"))
BUTTON_GPIOS = [
    int(value.strip())
    for value in os.getenv(
        "BUTTON_GPIOS_BCM", "17,27,22,5,6,26,16,25,18,12"
    ).split(",")
    if value.strip()
]

IDLE_BLUE = (0, 0, 35)
PRESSED_GREEN = (0, 55, 0)
OFF = (0, 0, 0)
CHASE_INTERVAL = 0.35
POLL_INTERVAL = 0.02


def validate_configuration() -> None:
    if RING_COUNT != 10:
        raise RuntimeError("O teste espera RING_COUNT=10.")
    if LEDS_PER_RING <= 0:
        raise RuntimeError("LEDS_PER_RING precisa ser maior que zero.")
    if len(BUTTON_GPIOS) != RING_COUNT or len(set(BUTTON_GPIOS)) != RING_COUNT:
        raise RuntimeError("BUTTON_GPIOS_BCM precisa ter 10 GPIOs diferentes.")
    conflicts = sorted({7, 8, 9, 10, 11}.intersection(BUTTON_GPIOS))
    if conflicts:
        raise RuntimeError(f"GPIOs {conflicts} estão reservados para o SPI0.")


def main() -> None:
    validate_configuration()
    total_leds = RING_COUNT * LEDS_PER_RING
    neo = Pi5Neo(
        SPI_DEVICE,
        num_leds=total_leds,
        spi_speed_khz=SPI_SPEED_KHZ,
        quiet_mode=True,
    )
    buttons: list[Button] = []
    previous_pressed = [False] * RING_COUNT
    last_frame: tuple[tuple[int, int, int], ...] | None = None

    def render(frame: tuple[tuple[int, int, int], ...]) -> None:
        nonlocal last_frame
        if frame == last_frame:
            return
        neo.clear_strip()
        for ring_index, color in enumerate(frame):
            first_pixel = ring_index * LEDS_PER_RING
            for pixel in range(first_pixel, first_pixel + LEDS_PER_RING):
                neo.set_led_color(pixel, *color)
        neo.update_strip(sleep_duration=0.001)
        last_frame = frame

    try:
        buttons = [
            Button(gpio, pull_up=True, bounce_time=0.04)
            for gpio in BUTTON_GPIOS
        ]

        print("Teste contínuo iniciado.")
        print("Azul: animação dos anéis | Verde: botoeira pressionada")
        for index, gpio in enumerate(BUTTON_GPIOS, start=1):
            print(f"Botoeira {index}: GPIO BCM {gpio}")
        print("Use CTRL+C para encerrar e apagar os LEDs.\n")

        chase_ring = -1
        next_chase = time.monotonic()

        while True:
            pressed = [button.is_pressed for button in buttons]

            for index, state in enumerate(pressed):
                if state != previous_pressed[index]:
                    action = "PRESSIONADA" if state else "SOLTA"
                    print(
                        f"{action}: botoeira {index + 1} — "
                        f"GPIO {BUTTON_GPIOS[index]}",
                        flush=True,
                    )
            previous_pressed = pressed

            if any(pressed):
                frame = tuple(
                    PRESSED_GREEN if state else OFF for state in pressed
                )
            else:
                now = time.monotonic()
                if now >= next_chase:
                    chase_ring = (chase_ring + 1) % RING_COUNT
                    next_chase = now + CHASE_INTERVAL
                frame = tuple(
                    IDLE_BLUE if index == chase_ring else OFF
                    for index in range(RING_COUNT)
                )

            render(frame)
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nTeste encerrado pelo usuário.")
    finally:
        for button in buttons:
            button.close()
        neo.clear_strip()
        neo.update_strip(sleep_duration=0.001)
        neo.close()
        print("Todos os LEDs foram apagados.")


if __name__ == "__main__":
    main()
