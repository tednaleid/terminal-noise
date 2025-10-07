#!/usr/bin/env -S uv run --script
# ABOUTME: Generates animated ASCII art using OpenSimplex noise algorithm.
# ABOUTME: Renders to terminal with automatic window size detection and 120 FPS animation.
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
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from opensimplex import OpenSimplex

# Character sets for rendering
CHARSETS = {
    'simple': ' .:-=+*#%@',
    'growth': ' .\'`,;:!|liI+~<>icv)(xr7t1{?[fjz}nsu*LJ#$%&0@',
    'dense': ' .\':`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
    'blocks': ' ░▒▓█',
    'box': ' ·│─┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬'
}

# Worker function for multiprocessing (must be at module level)
def _render_frame_worker(args):
    """Render a complete frame in a worker process."""
    width, height, scale, seed, charset, time_val, color_start, color_end = args

    # Each process creates its own OpenSimplex instance
    noise = OpenSimplex(seed=seed)

    if color_start is not None and color_end is not None:
        # Colored version
        lines = []
        for y in range(height):
            line_parts = []
            y_scaled = y * scale
            for x in range(width):
                noise_value = noise.noise3(x * scale, y_scaled, time_val)
                normalized = (noise_value + 1) * 0.5
                idx = int(normalized * (len(charset) - 1))

                r = int(color_start[0] + (color_end[0] - color_start[0]) * normalized)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * normalized)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * normalized)

                line_parts.append(f'\033[38;2;{r};{g};{b}m{charset[idx]}')
            lines.append(''.join(line_parts))
        return '\n'.join(lines) + '\033[0m'
    else:
        # Monochrome version
        lines = []
        for y in range(height):
            line_parts = []
            y_scaled = y * scale
            for x in range(width):
                noise_value = noise.noise3(x * scale, y_scaled, time_val)
                normalized = (noise_value + 1) * 0.5
                idx = int(normalized * (len(charset) - 1))
                line_parts.append(charset[idx])
            lines.append(''.join(line_parts))
        return '\n'.join(lines)

class TerminalNoise:
    def __init__(self, charset='simple', scale=0.1, seed=None, color_start=None, color_end=None, use_multiprocess=False, show_fps=False):
        if seed is None:
            seed = int(time.time())
        self.seed = seed
        self.noise = OpenSimplex(seed=seed)
        self.charset = CHARSETS.get(charset, CHARSETS['simple'])
        self.scale = scale
        self.time = 0.0
        self.running = True
        self.color_start = color_start
        self.color_end = color_end
        self.use_multiprocess = use_multiprocess
        self.show_fps = show_fps
        self.frame_times = []  # Rolling window of recent frame times

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl-C) for graceful shutdown."""
        self.running = False

    def get_terminal_size(self):
        """Get current terminal dimensions."""
        try:
            size = os.get_terminal_size()
            # Reserve two lines: one for FPS display, one to avoid scrolling
            reserve = 2 if self.show_fps else 1
            return size.columns, size.lines - reserve
        except OSError:
            # Fallback for when output is piped or redirected
            return 80, 24

    def calculate_fps(self, frame_duration):
        """Calculate current FPS based on recent frame times."""
        self.frame_times.append(frame_duration)
        # Keep only last 30 frames for rolling average
        if len(self.frame_times) > 30:
            self.frame_times.pop(0)

        if not self.frame_times:
            return 0.0

        avg_duration = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_duration if avg_duration > 0 else 0.0

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

        if self.color_start is not None and self.color_end is not None:
            # Colored version with optimized string building
            lines = []
            for y in range(height):
                line_parts = []
                y_scaled = y * self.scale
                for x in range(width):
                    noise_value = self.noise.noise3(x * self.scale, y_scaled, self.time)
                    normalized = (noise_value + 1) * 0.5  # Slightly faster than / 2
                    idx = int(normalized * (len(self.charset) - 1))

                    # Inline color calculation
                    r = int(self.color_start[0] + (self.color_end[0] - self.color_start[0]) * normalized)
                    g = int(self.color_start[1] + (self.color_end[1] - self.color_start[1]) * normalized)
                    b = int(self.color_start[2] + (self.color_end[2] - self.color_start[2]) * normalized)

                    line_parts.append(f'\033[38;2;{r};{g};{b}m{self.charset[idx]}')
                lines.append(''.join(line_parts))
            return '\n'.join(lines) + '\033[0m'
        else:
            # Monochrome version - much simpler
            lines = []
            for y in range(height):
                line_parts = []
                y_scaled = y * self.scale
                for x in range(width):
                    noise_value = self.noise.noise3(x * self.scale, y_scaled, self.time)
                    normalized = (noise_value + 1) * 0.5
                    idx = int(normalized * (len(self.charset) - 1))
                    line_parts.append(self.charset[idx])
                lines.append(''.join(line_parts))
            return '\n'.join(lines)

    def run(self, target_fps=120):
        """Main animation loop - chooses single or multiprocess based on settings."""
        if self.use_multiprocess:
            self.run_multiprocess(target_fps)
        else:
            self.run_single(target_fps)

    def run_single(self, target_fps=120):
        """Single-threaded animation loop."""
        frame_time = 1.0 / target_fps
        time_step = 0.05  # Amount to increment time each frame

        # Hide cursor
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()

        try:
            last_frame_time = time.time()
            while self.running:
                loop_start = time.time()

                # Move cursor to home position
                sys.stdout.write('\033[H')

                # Render and output frame
                frame = self.render_frame()
                sys.stdout.write(frame)

                # Display FPS if enabled (measure actual frame-to-frame time)
                if self.show_fps:
                    current_time = time.time()
                    frame_duration = current_time - last_frame_time
                    fps = self.calculate_fps(frame_duration)
                    sys.stdout.write(f'\n{fps:.2f}')
                    last_frame_time = current_time

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

    def run_multiprocess(self, target_fps=120):
        """Multiprocess animation loop with frame pipeline."""
        frame_time = 1.0 / target_fps
        time_step = 0.05
        buffer_size = cpu_count()  # Pre-render this many frames ahead

        width, height = self.get_terminal_size()

        # Hide cursor
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()

        try:
            with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                # Pre-populate the pipeline with future frames
                futures = []
                for i in range(buffer_size):
                    time_val = self.time + (i * time_step)
                    args = (width, height, self.scale, self.seed, self.charset,
                           time_val, self.color_start, self.color_end)
                    future = executor.submit(_render_frame_worker, args)
                    futures.append(future)

                frame_index = 0
                last_frame_time = time.time()
                while self.running:
                    loop_start = time.time()

                    # Get the next completed frame
                    frame = futures[0].result()
                    futures.pop(0)

                    # Display the frame
                    sys.stdout.write('\033[H')
                    sys.stdout.write(frame)

                    # Display FPS if enabled (measure actual frame-to-frame time)
                    if self.show_fps:
                        current_time = time.time()
                        frame_duration = current_time - last_frame_time
                        fps = self.calculate_fps(frame_duration)
                        sys.stdout.write(f'\n{fps:.2f}')
                        last_frame_time = current_time

                    sys.stdout.flush()

                    # Submit a new frame to maintain the pipeline
                    time_val = self.time + (buffer_size * time_step)
                    args = (width, height, self.scale, self.seed, self.charset,
                           time_val, self.color_start, self.color_end)
                    future = executor.submit(_render_frame_worker, args)
                    futures.append(future)

                    # Increment time
                    self.time += time_step
                    frame_index += 1

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
    parser.add_argument(
        '--multiprocess',
        action='store_true',
        help='Enable multiprocess rendering for higher FPS (uses all CPU cores)'
    )
    parser.add_argument(
        '--show-fps',
        action='store_true',
        help='Display current FPS on the last line of output'
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
        color_end=color_end,
        use_multiprocess=args.multiprocess,
        show_fps=args.show_fps
    )
    noise_gen.run()

if __name__ == '__main__':
    main()
