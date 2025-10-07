# terminal-noise

A terminal-based animated noise visualization using the OpenSimplex algorithm. Renders smooth, organic patterns as ASCII art with optional RGB color gradients.

## Requirements

- Python 3.12+
- `uv` package manager

## Installation

The script is self-contained and uses `uv` to manage dependencies automatically. No separate installation is required.

## Usage

Make the script executable and run it:

```bash
chmod +x terminal-noise.py
./terminal-noise.py
```

The animation will fill your terminal window and run until you press Ctrl-C.

## Command Line Arguments

### Character Sets (`-c`, `--charset`)

- `simple` - Basic gradient (default): ` .:-=+*#%@`
- `growth` - Characters that grow from small to dense
- `dense` - High-detail character set with many gradations
- `blocks` - Block characters: ` ░▒▓█`
- `box` - Box drawing characters for geometric patterns

### Noise Scale (`-s`, `--scale`)

Controls the detail level of the noise. Default is `0.1`.

- Smaller values (e.g., `0.05`) = more detailed, busier patterns
- Larger values (e.g., `0.3`) = smoother, flowing patterns

### Color Options

- `--color-start` - Starting color in hex format (default: `#00CED1`)
- `--color-end` - Ending color in hex format (default: `#FF8C00`)
- `--no-color` - Disable colors for monochrome output

## Example Commands

Basic usage with default settings:
```bash
./terminal-noise.py
```

Monochrome with block characters:
```bash
./terminal-noise.py -c blocks --no-color
```

Smooth flowing animation:
```bash
./terminal-noise.py -s 0.2
```

Detailed noise with growth characters:
```bash
./terminal-noise.py -c growth -s 0.05
```

### Color Gradient Examples

Ocean theme (deep blue to cyan):
```bash
./terminal-noise.py --color-start '#000080' --color-end '#00FFFF'
```

Fire theme (red to yellow):
```bash
./terminal-noise.py --color-start '#8B0000' --color-end '#FFD700'
```

Forest theme (dark green to lime):
```bash
./terminal-noise.py --color-start '#013220' --color-end '#32CD32'
```

Sunset theme (purple to orange):
```bash
./terminal-noise.py --color-start '#4B0082' --color-end '#FF8C00' -s 0.15
```

Neon theme (magenta to cyan):
```bash
./terminal-noise.py -c box --color-start '#FF00FF' --color-end '#00FFFF' -s 0.12
```

Matrix theme (black to green with dense characters):
```bash
./terminal-noise.py -c dense --color-start '#000000' --color-end '#00FF00' -s 0.08
```

## Recording Output

The animation uses ANSI escape codes, so you can record it to a file and replay it:

```bash
# Record 5 seconds of animation
timeout 5 ./terminal-noise.py > output.ans

# Replay the recording
cat output.ans
```

## How It Works

The script uses a 3D OpenSimplex noise field with dimensions (x, y, time). Each frame:

1. Samples the noise at each terminal position
2. Maps noise values (-1 to 1) to character indices
3. Optionally applies color interpolation based on noise value
4. Renders using ANSI escape codes for efficient redrawing

The time dimension increments each frame, creating smooth morphing animations.

## Performance

The animation runs at approximately 25-30 FPS on an 80x24 terminal, which provides smooth organic motion. Performance scales with terminal size - smaller terminals or larger scale values will render faster. The primary bottleneck is noise generation (each frame requires ~1,920 noise calculations for a standard terminal).

Tips for better performance:
- Use larger `--scale` values (e.g., `0.2` or `0.3`) for fewer calculations per visible change
- Use `--no-color` for monochrome mode (slightly faster)
- Smaller terminal windows render faster
