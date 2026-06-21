Examples
========

150 keV thermionic electron gun
-------------------------------

A planar-diode electron gun, in ``examples/thermionic_gun/``. Electrons are
emitted thermionically from a hot cathode and accelerated across a 2 cm vacuum
gap by a 150 kV bias, with self-consistent space-charge and self-magnetic
fields solved by the labframe electromagnetostatic Multigrid solver
(``ES_MLMG_EMS``). Emission is pulsed for 20 ps.

Geometry (2-D Cartesian — WarpX names the in-plane axes ``x`` and ``z``):

- ``z = 0`` — cathode, ``phi = 0`` V
- ``z = 0.02 m`` — anode, ``phi = 150 kV`` → electrons gain 150 keV
- ``x`` — transverse; PEC side walls enclose the diode

.. note::

   The transverse walls are PEC (``dirichlet``), **not** periodic, on purpose:
   the magnetostatic vector-potential solve diverges with a periodic transverse
   boundary, but a fully PEC-enclosed diode is well-posed for the MLMG solver.

Running
~~~~~~~

.. code-block:: bash

   cd examples/thermionic_gun
   python run.py

This steps the simulation to 300 ps and writes diagnostics under
``output/diags/`` plus three plots:

- ``phase_space_z_KE.png`` — longitudinal phase space (``z`` vs. kinetic
  energy); the beam streams toward the anode and approaches 150 keV.
- ``centroid_z_vs_t.png`` — beam centroid position vs. time.
- ``potential_xz.png`` — the electrostatic potential ``phi`` over the diode.

The driver script
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from warpx import WarpX

   w = WarpX(input_file="gun.yaml", path="output", verbose=True)
   w.run()

   w.plot2D("z", "kinetic_energy").savefig("phase_space_z_KE.png")
   w.plot1D("t", "mean_z").savefig("centroid_z_vs_t.png")
   w.plot_fields("phi", "x", "z").savefig("potential_xz.png")

The full input file (``gun.yaml``) and a longer write-up live in
``examples/thermionic_gun/``. See :doc:`configuration` for the YAML reference.
