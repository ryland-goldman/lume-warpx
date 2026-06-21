LUME-WarpX
==========

**LUME-WarpX** is a `LUME-compatible <https://slaclab.github.io/lume-base/>`_
wrapper for `WarpX <https://warpx.readthedocs.io/en/latest/index.html>`_, the
exascale particle-in-cell code for accelerator, plasma, and laser-plasma
simulations.

It exposes a single :class:`~warpx.warpx.WarpX` class that:

- builds a complete WarpX/PICMI simulation from a declarative **YAML input
  file** — grid, field solver, applied fields, particle species, and
  diagnostics;
- **runs** the simulation through the familiar LUME ``configure`` / ``run``
  lifecycle;
- **archives and restores** the full input and openPMD output to a single HDF5
  file; and
- **plots** fields and particle phase space directly from the openPMD
  diagnostics, backed by
  `openPMD-beamphysics <https://github.com/ChristopherMayes/openPMD-beamphysics>`_.

.. note::

   Development is in progress. WarpX (``pywarpx``) is **not** available on PyPI
   and must be built from source — see :doc:`installation`.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   quickstart
   configuration
   plotting
   archiving
   examples
   api

Quick example
-------------

.. code-block:: python

   from warpx import WarpX

   w = WarpX(input_file="gun.yaml", path="./output", verbose=True)
   w.run()  # configures, steps the simulation, and loads every diagnostic

   w.plot2D("z", "kinetic_energy")   # longitudinal phase space
   w.plot1D("t", "mean_z")           # beam centroid vs. time
   w.plot_fields("phi", "x", "z")    # electrostatic potential map
