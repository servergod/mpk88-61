#!/usr/bin/env python3
"""
Send a .syx file to a raw ALSA MIDI device in chunks, matching the classic
MIDI-OX buffer/delay mechanism: write N bytes, pause, write N bytes, pause,
then an extra pause after the final F7.

Usage: chunked_sysex_send.py <file.syx> <device> <chunk_bytes> <delay_ms> <delay_after_f7_ms>
"""
import sys
import time

def main():
    path, device, chunk, delay_ms, delay_f7_ms = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    delay = delay_ms / 1000.0
    delay_f7 = delay_f7_ms / 1000.0

    data = open(path, "rb").read()
    n_chunks = (len(data) + chunk - 1) // chunk
    est = n_chunks * delay
    print(f"{len(data)} bytes, {chunk}-byte chunks -> {n_chunks} chunks, "
          f"{delay_ms}ms between chunks, {delay_f7_ms}ms after F7", file=sys.stderr)
    print(f"Estimated time: {est:.1f}s ({est/60:.1f} min)", file=sys.stderr)

    with open(device, "wb", buffering=0) as f:
        start = time.time()
        for i in range(0, len(data), chunk):
            piece = data[i:i+chunk]
            f.write(piece)
            print(f"\r{i+len(piece)}/{len(data)} bytes ({time.time()-start:.0f}s)",
                  end="", file=sys.stderr)
            time.sleep(delay)
        time.sleep(delay_f7)
        print(f"\nDone. {time.time()-start:.0f}s total", file=sys.stderr)

if __name__ == "__main__":
    main()
