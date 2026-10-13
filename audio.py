"""Render short General MIDI notes with the system FluidSynth SoundFont."""

from __future__ import annotations

import ctypes as c
import io
import threading
import wave
from functools import lru_cache
from pathlib import Path


SOUNDFONT = Path('/usr/share/sounds/sf2/FluidR3_GM.sf2')
SAMPLE_RATE = 44100
PROGRAMS = {0, 4, 24, 48, 73, 80}


class SoundFontRenderer:
    def __init__(self):
        if not SOUNDFONT.is_file():
            raise RuntimeError(f'SoundFont missing: {SOUNDFONT}')
        self.lib = c.CDLL('libfluidsynth.so.3')
        self._bind()
        self.settings = self.lib.new_fluid_settings()
        if not self.settings:
            raise RuntimeError('FluidSynth settings could not be created')
        self.lib.fluid_settings_setnum(self.settings, b'synth.sample-rate', SAMPLE_RATE)
        self.lib.fluid_settings_setnum(self.settings, b'synth.gain', 0.6)
        self.synth = self.lib.new_fluid_synth(self.settings)
        if not self.synth:
            raise RuntimeError('FluidSynth could not start')
        if self.lib.fluid_synth_sfload(self.synth, str(SOUNDFONT).encode(), 1) < 0:
            raise RuntimeError('General MIDI SoundFont could not load')
        self.lock = threading.RLock()

    def _bind(self):
        lib = self.lib
        signatures = {
            'new_fluid_settings': (c.c_void_p, []),
            'fluid_settings_setnum': (c.c_int, [c.c_void_p, c.c_char_p, c.c_double]),
            'new_fluid_synth': (c.c_void_p, [c.c_void_p]),
            'fluid_synth_sfload': (c.c_int, [c.c_void_p, c.c_char_p, c.c_int]),
            'fluid_synth_program_change': (c.c_int, [c.c_void_p, c.c_int, c.c_int]),
            'fluid_synth_noteon': (c.c_int, [c.c_void_p, c.c_int, c.c_int, c.c_int]),
            'fluid_synth_noteoff': (c.c_int, [c.c_void_p, c.c_int, c.c_int]),
            'fluid_synth_all_sounds_off': (c.c_int, [c.c_void_p, c.c_int]),
            'fluid_synth_write_s16': (c.c_int, [c.c_void_p, c.c_int, c.c_void_p, c.c_int, c.c_int,
                                               c.c_void_p, c.c_int, c.c_int]),
        }
        for name, (restype, argtypes) in signatures.items():
            fn = getattr(lib, name)
            fn.restype = restype
            fn.argtypes = argtypes

    @lru_cache(maxsize=256)
    def render(self, program: int, note: int) -> bytes:
        if program not in PROGRAMS or not 36 <= note <= 95:
            raise ValueError('Unsupported instrument or note')
        with self.lock:
            self.lib.fluid_synth_all_sounds_off(self.synth, 0)
            self.lib.fluid_synth_program_change(self.synth, 0, program)
            self.lib.fluid_synth_noteon(self.synth, 0, note, 100)
            attack = self._samples(round(SAMPLE_RATE * 0.85))
            self.lib.fluid_synth_noteoff(self.synth, 0, note)
            release = self._samples(round(SAMPLE_RATE * 0.35))
        out = io.BytesIO()
        with wave.open(out, 'wb') as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(attack + release)
        return out.getvalue()

    def _samples(self, frames: int) -> bytes:
        left = (c.c_int16 * frames)()
        right = (c.c_int16 * frames)()
        status = self.lib.fluid_synth_write_s16(self.synth, frames, left, 0, 1, right, 0, 1)
        if status != 0:
            raise RuntimeError(f'Audio rendering failed: {status}')
        stereo = (c.c_int16 * (frames * 2))()
        stereo[0::2] = left
        stereo[1::2] = right
        return bytes(stereo)
