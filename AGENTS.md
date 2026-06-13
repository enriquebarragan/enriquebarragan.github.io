# AGENTS.md

## Project

This is a GitHub Pages site built with Jekyll.

## Setup and Verification

- Prefer Docker for local Jekyll commands. Do not assume Ruby or Bundler are installed on the host.
- To build the site, run:

  ```powershell
  docker run --rm -v "${PWD}:/site" -w /site ruby:3.2 bash -lc "bundle install && bundle exec jekyll build"
  ```

- If running a local preview, use the Docker command from `README.md`.
- Do not edit generated files under `_site/` directly.

## Publishing

- GitHub Pages builds from the source files. Commit source changes, not `_site/` output.