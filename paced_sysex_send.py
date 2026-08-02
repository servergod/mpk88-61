#!/usr/bin/env python3
"""
Send a .syx file to a raw ALSA MIDI device, paced at a fixed bit rate,
one byte at a time, to avoid overwhelming a bootloader with no flow control.

Usage: paced_sysex_send.py <file.syx> <alsa-rawmidi-device> <bits-per-second>
Example: paced_sysex_send.py MPK61_v1_01_id77.syx /dev/snd/midiC1D0 150
"""
import sys
import time

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    path, device, bps = sys.argv[1], sys.argv[2], float(sys.argv[3])
    delay = 8.0 / bps  # seconds per byte (8 bits/byte)

    data = open(path, "rb").read()
    print(f"Sending {len(data)} bytes to {device} at {bps} bps "
          f"({delay*1000:.1f} ms/byte)", file=sys.stderr)
    est_seconds = len(data) * delay
    print(f"Estimated total time: {est_seconds:.0f}s "
          f"({est_seconds/60:.1f} min)", file=sys.stderr)

    with open(device, "wb", buffering=0) as f:
        start = time.time()
        for i, b in enumerate(data):
            f.write(bytes([b]))
            if i % 500 == 0:
                elapsed = time.time() - start
                print(f"\r{i}/{len(data)} bytes ({elapsed:.0f}s elapsed)",
                      end="", file=sys.stderr)
            time.sleep(delay)
        print(f"\nDone. {len(data)} bytes sent in {time.time()-start:.0f}s",
              file=sys.stderr)

if __name__ == "__main__":
    main()
