## High-Level Goal

Uses the OpenSimplex noise algorithm to generate noise that we render as ASCII to the terminal.

The rendered result will be animated ASCII. As the noise changes, it will morph from one representation to the next.

## Requirments

- run as a python command line app that leverages `uv` to launch as a standalone script via a `uv` shebang.
- Possible python library for OpenSimplex noise: https://pypi.org/project/opensimplex/
- runs at least at 60 FPS
- should run until ctrl-c/sigint is sent

## Stretch Goals
- Allow the user some control over the character set used to render
- Allow the user to pick different gradients to change the appearance


## Working Requirements
- automatically commit after major changes

## Questions
- can/should we allow piping to a file so that it can be examined/replayed? Depending on how the screen is redrawn this might not work well (or might be great)