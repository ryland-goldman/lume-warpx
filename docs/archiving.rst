Archiving & restoring
=====================

A full run — its input and all openPMD diagnostics — can be serialised to a
single HDF5 file and later restored, in the LUME ``archive`` / ``load_archive``
style.

Archiving
---------

.. code-block:: python

   w = WarpX(input_file="gun.yaml", path="./output")
   w.run()

   w.archive()                 # writes warpx_<fingerprint>.h5
   w.archive("my_run.h5")      # or a path you choose
   w.archive(h5_group)         # or into an open h5py.File / group

The archive stores:

- ``fingerprint`` and ``finished`` flags as attributes;
- the parsed input as JSON under ``input``;
- under ``output/files``, a byte-for-byte copy of every file in the
  diagnostics directory, plus the list of iterations.

:meth:`~warpx.warpx.WarpX.archive` returns the ``h5py`` object it wrote to.

.. note::

   To archive output you must have loaded it first (``run()`` does this, or call
   :meth:`~warpx.warpx.WarpX.load_output`). Archiving fails if the diagnostics
   directory is unknown or missing.

Restoring
---------

.. code-block:: python

   w = WarpX()
   w.load_archive("my_run.h5")     # restores input + diagnostics, then configures
   w.load_archive("my_run.h5", configure=False)  # skip re-configuring

Restoring unpacks the diagnostics into a fresh temporary directory, re-discovers
every openPMD series (so the plotting helpers work immediately), reloads the
input, and — unless ``configure=False`` — rebuilds the PICMI simulation.

.. code-block:: python

   w.load_archive("my_run.h5")
   w.plot2D("z", "kinetic_energy")   # plot straight from the restored output
