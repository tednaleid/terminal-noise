## High-Level Goal

Uses the OpenSimplex noise algorithm to generate noise that we render as ASCII to the terminal.

The rendered result will be animated ASCII. As the noise changes, it will morph from one representation to the next.

## Requirements

- run as a python command line app that leverages `uv` to launch as a standalone script via a `uv` shebang
- Possible python library for OpenSimplex noise: https://pypi.org/project/opensimplex/
- runs at least at 60 FPS
- should run until ctrl-c/sigint is sent
- automatically detect and fill the current terminal window size
- use 3D noise field (x, y, time) where time increments each frame for animation
- use ANSI escape codes (cursor positioning) for clearing/redrawing so output can be piped to file and replayed
- monochrome ASCII for v1 (ANSI color codes planned for v2)

## Command Line Arguments

- `--charset` or `-c`: Select character set for rendering
  - `simple`: ` .:-=+*#%@` (default)
  - `growth`: `` .'`,;:!|liI+~<>icv)(xr7t1{?[fjz}nsu*LJ#$%&0@`` - characters that "grow" from small to dense, progressing from the same visual point
  - `dense`: `` .':`^",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$``
  - `blocks`: ` ░▒▓█`
  - `box`: ` ·│─┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬` - uses box drawing characters (Unicode 179-218) for structured patterns
- `--scale` or `-s`: Noise scale factor (default: 0.1)
  - smaller values = more detailed/busy
  - larger values = smoother/flowing

## Stretch Goals
- Allow the user to pick different gradients/colors (ANSI color codes for v2)

## Working Requirements
- automatically commit after major changes
- keep SPEC.md updated with decisions and requirements