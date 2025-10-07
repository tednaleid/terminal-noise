#!/usr/bin/env -S uv run --script
# ABOUTME: Generates animated ASCII art using OpenSimplex noise algorithm.
# ABOUTME: Renders to terminal with automatic window size detection and 60 FPS animation.
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "opensimplex",
# ]
# ///

import argparse
import os
import signal
import sys
import time
from opensimplex import OpenSimplex

# Character sets for rendering
CHARSETS = {
    'simple': ' .:-=+*#%@',
    'growth': ' .\'`,;:!|liI+~<>icv)(xr7t1{?[fjz}nsu*LJ#$%&0@',
    'dense': ' .\':`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
    'blocks': ' ░▒▓█',
    'box': ' ·│─┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬'
}

class TerminalNoise:
    def __init__(self, charset='simple', scale=0.1, seed=None, color_start=None, color_end=None):
        if seed is None:
            seed = int(time.time())
        self.noise = OpenSimplex(seed=seed)
        self.charset = CHARSETS.get(charset, CHARSETS['simple'])
        self.scale = scale
        self.time = 0.0
        self.running = True
        self.color_start = color_start
        self.color_end = color_end

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl-C) for graceful shutdown."""
        self.running = False

    def get_terminal_size(self):
        """Get current terminal dimensions."""
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines - 1  # Reserve one line to avoid scrolling
        except OSError:
            # Fallback for when output is piped or redirected
            return 80, 24

    def interpolate_color(self, t):
        """Interpolate between start and end colors based on parameter t (0 to 1)."""
        if self.color_start is None or self.color_end is None:
            return None

        r = int(self.color_start[0] + (self.color_end[0] - self.color_start[0]) * t)
        g = int(self.color_start[1] + (self.color_end[1] - self.color_start[1]) * t)
        b = int(self.color_start[2] + (self.color_end[2] - self.color_start[2]) * t)
        return (r, g, b)

    def noise_to_char(self, noise_value):
        """Convert noise value (-1 to 1) to a character from the charset, with optional color."""
        # Normalize from [-1, 1] to [0, 1]
        normalized = (noise_value + 1) / 2
        # Map to character index
        idx = int(normalized * (len(self.charset) - 1))
        char = self.charset[idx]

        # Apply color if enabled
        if self.color_start is not None and self.color_end is not None:
            rgb = self.interpolate_color(normalized)
            # ANSI 24-bit true color: \033[38;2;R;G;Bm
            return f'\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{char}'

        return char

    def render_frame(self):
        """Generate and render a single frame of noise."""
        width, height = self.get_terminal_size()

        lines = []
        for y in range(height):
            line = []
            for x in range(width):
                # Sample 3D noise (x, y, time)
                noise_value = self.noise.noise3(
                    x * self.scale,
                    y * self.scale,
                    self.time
                )
                line.append(self.noise_to_char(noise_value))
            lines.append(''.join(line))

        # Reset color at end of frame if using colors
        frame = '\n'.join(lines)
        if self.color_start is not None and self.color_end is not None:
            frame += '\033[0m'  # Reset all attributes

        return frame

    def run(self, target_fps=120):
        """Main animation loop."""
        frame_time = 1.0 / target_fps
        time_step = 0.05  # Amount to increment time each frame

        # Hide cursor
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()

        try:
            while self.running:
                loop_start = time.time()

                # Move cursor to home position
                sys.stdout.write('\033[H')

                # Render and output frame
                frame = self.render_frame()
                sys.stdout.write(frame)
                sys.stdout.flush()

                # Increment time for next frame
                self.time += time_step

                # Sleep to maintain target FPS
                elapsed = time.time() - loop_start
                sleep_time = frame_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        finally:
            # Show cursor and move to bottom
            sys.stdout.write('\033[?25h')
            sys.stdout.write('\n')
            sys.stdout.flush()

def parse_hex_color(hex_str):
    """Convert hex color string (e.g., '#FF5733' or 'FF5733') to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        raise ValueError(f'Invalid hex color: {hex_str}. Must be 6 hex digits.')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def main():
    parser = argparse.ArgumentParser(
        description='Generate animated ASCII art using OpenSimplex noise.'
    )
    parser.add_argument(
        '-c', '--charset',
        choices=list(CHARSETS.keys()),
        default='simple',
        help='Character set to use for rendering (default: simple)'
    )
    parser.add_argument(
        '-s', '--scale',
        type=float,
        default=0.1,
        help='Noise scale factor - smaller is more detailed, larger is smoother (default: 0.1)'
    )
    parser.add_argument(
        '--color-start',
        type=str,
        default='#00CED1',
        help='Starting color for gradient in hex format (default: #00CED1 - dark cyan)'
    )
    parser.add_argument(
        '--color-end',
        type=str,
        default='#FF8C00',
        help='Ending color for gradient in hex format (default: #FF8C00 - dark orange)'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable color gradient (monochrome mode)'
    )

    args = parser.parse_args()

    # Parse colors if not in monochrome mode
    color_start = None
    color_end = None
    if not args.no_color:
        try:
            color_start = parse_hex_color(args.color_start)
            color_end = parse_hex_color(args.color_end)
        except ValueError as e:
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)

    noise_gen = TerminalNoise(
        charset=args.charset,
        scale=args.scale,
        color_start=color_start,
        color_end=color_end
    )
    noise_gen.run()

if __name__ == '__main__':
    main()
