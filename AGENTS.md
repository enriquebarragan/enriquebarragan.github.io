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

## 3D Assets

- GLB files under `assets/3d/custom/` are user-created source models. They may be large and should be optimized before being used on the homepage.
- Use `@gltf-transform/cli` through `npx.cmd` on Windows. Example:

  ```powershell
  npx.cmd --yes @gltf-transform/cli optimize assets/3d/custom/source.glb assets/3d/custom/source.optimized.glb --simplify-ratio 0.12 --simplify-error 0.02 --texture-compress false
  ```

- Homepage code should load the optimized custom GLB, not the large source GLB. Add the large custom source file to `_config.yml` `exclude` so GitHub Pages does not publish it.
- Non-custom directories under `assets/3d/` usually contain third-party GLBs and may include a `license.txt`. If a model with a license is shown on the homepage, include a small credit line under the 3D stage using the license text.
- If an optimized GLB uses `EXT_meshopt_compression`, keep `MeshoptDecoder` wired into the Three.js `GLTFLoader`.

## Publishing

- GitHub Pages builds from the source files. Commit source changes, not `_site/` output.
