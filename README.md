# LUME-WarpX

[![Documentation Status](https://readthedocs.org/projects/lume-warpx/badge/?version=latest)](https://lume-warpx.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://img.shields.io/pypi/v/lume-warpx.svg)](https://pypi.org/project/lume-warpx/)
[![PyPI downloads](https://img.shields.io/pypi/dm/lume-warpx.svg)](https://pypi.org/project/lume-warpx/)

A [LUME-compatible](https://slaclab.github.io/lume-base/) wrapper for the [WarpX](https://warpx.readthedocs.io/en/latest/index.html) particle-in-cell accelerator simulation code. Development is still in-progress.

A simulation is defined by a static YAML config (grid / solver / simulation / fields / species / diagnostics) passed to `WarpX(input_file=...)`. Beyond the declarative config, the wrapper supports:

- **`AppliedFromFile`** fields — tabulated, per-step applied E/B maps (`picmi.LoadAppliedField`) with `warpx_E/B_time_function` parser-string scaling (RF cavities, solenoids).
- **`FromInitialParticles`** species — inject a `ParticleGroup` passed as `WarpX(initial_particles=...)` (optionally seeding only the first `n_seed`).
- **runtime overrides** — `get` / `set` / `update` patch the loaded config before `configure()` so a driver can compute values (time functions, `max_steps`, periods) and read constants back.
- **callbacks + progress** — `install_callback("beforestep", fn)` for time-release injection; `run(progress="label")` for a tqdm bar.
- **plotting** — `plot2D` (phase space), `plot1D` (slice stats / trends), `plot_fields` (field planes).

See `docs/configuration.rst` for the full reference.