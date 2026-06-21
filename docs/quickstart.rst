Quickstart
==========

LUME-WarpX follows the standard `LUME <https://slaclab.github.io/lume-base/>`_ operation.

Usage
-------------

.. code-block:: python

   from warpx import WarpX

   # 1. Construct from a YAML input file.
   w = WarpX(input_file="gun.yaml", path="./output", verbose=True)

   # 2. Run the simulation.
   w.run()

   # 3. Inspect / plot.
   w.plot2D("z", "kinetic_energy")

Constructor options
--------------------

.. code-block:: python

   WarpX(
       input_file=None,    # path to the YAML simulation definition
       initial_particles=None,
       verbose=False,      # print progress (and set WarpX verbosity)
       timeout=None,
       workdir=None,       # working directory (used when path is unset)
       path=None,          # where diagnostics are written: <path>/diags
   )

- **path** — the run directory. Diagnostics are always written to
  ``<path>/diags``. If omitted, ``workdir`` is used; if that is also omitted, a
  temporary directory (``warpx_*``) is created.
- **verbose** — when ``True``, LUME-WarpX prints lifecycle messages and runs
  WarpX with verbosity enabled.

Working with output
--------------------

After ``run()`` (or :meth:`~warpx.warpx.WarpX.load_output`), every openPMD
diagnostic series under ``<path>/diags`` is loaded into a dictionary of
``openpmd_viewer.OpenPMDTimeSeries`` objects. The plotting helpers locate the
right series automatically:

.. code-block:: python

   w.load_output()                  # re-discover all diagnostic series
   w.load_output("output/diags/diag1")  # load a single series by directory

   w.plot_fields("Ez", "x", "z")    # field map from the field diagnostic
   w.plot1D("z", "sigma_x")         # transverse size along the bunch
   w.plot2D("x", "px")              # transverse phase space

See :doc:`plotting` for the full plotting reference and :doc:`configuration`
for the YAML input format.
