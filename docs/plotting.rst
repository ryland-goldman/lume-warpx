Plotting & analysis
===================

Once output is loaded (automatically by :meth:`~warpx.warpx.WarpX.run`, or
manually with :meth:`~warpx.warpx.WarpX.load_output`), three helpers turn the
openPMD diagnostics into Matplotlib figures. Each returns the
``matplotlib.figure.Figure`` so you can save or further customise it.

All three locate the correct diagnostic series automatically — you do not pass a
series name. Particle plots build an
`openPMD-beamphysics <https://github.com/ChristopherMayes/openPMD-beamphysics>`_
``ParticleGroup`` under the hood.

plot_fields — field maps
-------------------------

.. code-block:: python

   w.plot_fields(field, x, y, iteration=None, theta=0.0, m="all", ax=None, **kwargs)

Plots a 2-D field over the ``x``–``y`` plane as an ``imshow`` heatmap.

- **field** — a field name from :attr:`WarpX.available.fields.list
  <warpx.warpx.WarpX.available>`: ``E``, ``Ex``…``Ez``, ``Er``, ``Etheta``,
  ``Emag`` (and the ``B``/``J`` equivalents), ``rho``, ``phi``. A bare vector
  name (``E``, ``B``, ``J``) is plotted as its magnitude.
- **x, y** — the two plane axes (from ``x``, ``y``, ``z``, ``r``, ``theta``);
  the remaining axis is sliced through.
- **iteration** — defaults to the last available dump.
- **theta**, **m** — azimuthal angle / mode for ``thetaMode`` (cylindrical)
  geometry.
- **ax** — an existing axis to draw into; otherwise a new figure is created.

.. code-block:: python

   fig = w.plot_fields("phi", "x", "z")
   fig.savefig("potential_xz.png", dpi=140, bbox_inches="tight")

plot1D — statistic vs. coordinate
----------------------------------

.. code-block:: python

   w.plot1D(x, y, species=None, iteration=None, select=None, n_slice=50, **kwargs)

Plots a beam statistic ``y`` either **along the bunch** (sliced by coordinate
``x``) or **over time** (``x="t"``).

- **x** — slice coordinate: ``x``, ``y``, ``z``, ``r``, ``theta``, or ``t``.
  With ``t``, the statistic is computed at every dump and plotted vs. time.
- **y** — a statistic, written ``<stat>_<coord>``:

  - statistics: ``mean``, ``sigma`` (alias ``std``), ``min``, ``max``,
    ``ptp``, ``delta``
  - covariance: ``cov_<a>__<b>`` (e.g. ``cov_x__px``)
  - scalars (no coordinate): ``norm_emit_x``, ``norm_emit_y``,
    ``norm_emit_4d``, ``charge``, ``n_particle``

- **species** — which species (defaults to the first with particles).
- **select** — a beamphysics selection dict to filter particles.
- **n_slice** — number of slices along ``x`` (ignored when ``x="t"``).

.. code-block:: python

   w.plot1D("z", "sigma_x")     # transverse size along the bunch
   w.plot1D("t", "mean_z")      # centroid position vs. time
   w.plot1D("z", "norm_emit_x") # slice emittance along z

plot2D — phase space
--------------------

.. code-block:: python

   w.plot2D(x, y, species=None, iteration=None, select=None, bins=None, **kwargs)

Plots a 2-D histogram of one coordinate against another (phase space).

- **x, y** — any of the :attr:`plot2D coordinates
  <warpx.warpx.WarpX.available>`: positions (``x``/``y``/``z``/``r``/``theta``),
  momenta (``px``…``ptheta``), ``kinetic_energy``, ``energy``, ``gamma``,
  ``beta``, ``p``, divergences ``xp``/``yp``, and ``Lz``.
- **bins** — histogram resolution.
- **species**, **iteration**, **select** — as above.

.. code-block:: python

   w.plot2D("z", "kinetic_energy")  # longitudinal phase space
   w.plot2D("x", "px")              # transverse phase space

Selecting particles
-------------------

``select`` is passed straight to openPMD-viewer / beamphysics, so you can filter
on any record component, e.g.:

.. code-block:: python

   w.plot2D("x", "px", select={"z": [0.018, 0.02]})  # only near the anode
