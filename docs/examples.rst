Examples
========

Each example lives in its own directory under ``examples/`` with a YAML input
file, a ``run.py`` driver, and a ``README.md``. Every one follows the same
pattern — construct a :class:`~warpx.warpx.WarpX` from the YAML, ``run()``, and
plot from the openPMD diagnostics:

.. code-block:: bash

   cd examples/<name>
   python run.py

See :doc:`configuration` for the YAML reference and :doc:`plotting` for the
plotting helpers.

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

1-D Pierce diode (Child-Langmuir limit)
---------------------------------------

A classic 1-D Pierce diode, in ``examples/pierce_diode/``, validating WarpX
against the Child-Langmuir space-charge law. Two parallel conducting plates 8 cm
apart hold a -93 kV difference. A potassium-ion (K+) beam is flux-injected from
the cathode at the space-charge-limited current density predicted by the
Child-Langmuir law and accelerated across the gap, arriving with ~93 keV.

- **Cold flux injection** — ions enter with a ``UniformFlux`` distribution and
  zero momentum spread, continuously refilling the gap.
- **Electrostatic MLMG solver** — the self-consistent space-charge potential
  uses the labframe electrostatic Multigrid solver (``ES_MLMG_LF``).
- **Non-standard species** — ``ions`` (K+) sets an explicit ``mass`` (39 m_u)
  and ``charge`` (+q_e); the wrapper reads these from the openPMD output so the
  kinetic-energy plots are computed correctly.

Running
~~~~~~~

.. code-block:: bash

   cd examples/pierce_diode
   python run.py

This steps the simulation for 5000 steps and writes:

- ``phase_space_z_KE.png`` — longitudinal phase space (``z`` vs. kinetic
  energy); the ions accelerate across the gap and approach ~93 keV at the anode.
- ``pz_profile_z.png`` — longitudinal momentum vs. position, the acceleration
  profile as the ions fall through the potential.
- ``n_particle_vs_t.png`` — beam population vs. time, building up to the
  steady-state space-charge-limited current.

The driver script
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from warpx import WarpX

   w = WarpX(input_file="pierce_diode.yaml", path="output", verbose=True)
   w.run()

   w.plot2D("z", "kinetic_energy", species="ions").savefig("phase_space_z_KE.png")
   w.plot2D("z", "pz", species="ions").savefig("pz_profile_z.png")
   w.plot1D("t", "n_particle", species="ions").savefig("n_particle_vs_t.png")

.. note::

   The canonical 1-D Pierce-diode result, the potential profile
   ``phi(z) ~ z^(4/3)``, is not plotted: ``plot_fields`` produces 2-D heatmaps
   and needs two distinct spatial plane axes, which a 1-D grid does not have. A
   particle diagnostic (added beyond the upstream example, which dumps no
   particles) is used to visualize the ion beam instead.

Beam-driven plasma wakefield acceleration (3-D)
-----------------------------------------------

A beam-driven plasma wakefield accelerator (PWFA), in
``examples/plasma_acceleration/``, ported from the WarpX
``inputs_test_3d_plasma_acceleration_picmi.py`` reference input. A dense,
relativistic electron drive beam streams along ``+z`` through a uniform cold
background plasma, expelling plasma electrons and driving a trailing
longitudinal accelerating field ``Ez`` — the heart of plasma-based acceleration.

- **Relativistic drive beam** — a transversely narrow electron bunch
  (``density = 1e23``) with a proper velocity of ``1e9`` m/s (PICMI proper
  velocity ``gamma*beta*c``, which legitimately exceeds c).
- **Moving window** — the box follows the beam at the speed of light
  (``moving_window_velocity = [0, 0, c]``), tracking the wake.
- **EM (Yee) solver** — finite-difference time-domain Maxwell solve
  (``EM_Yee``, ``cfl = 1.0``) with charge-conserving Esirkepov current
  deposition, matching the reference input.

The 3-D PICMI variant is used so the 2-D field heatmap has two in-plane spatial
axes to slice (``x``-``z`` through ``y = 0``).

Running
~~~~~~~

.. code-block:: bash

   cd examples/plasma_acceleration
   python run.py

This steps the simulation for 10 steps and writes:

- ``wakefield_Ez_xz.png`` — the longitudinal accelerating field ``Ez`` over the
  ``x``-``z`` plane (slice through ``y = 0``), showing the wake behind the beam.
- ``phase_space_beam_z_pz.png`` — drive-beam longitudinal phase space
  (``z`` vs. ``pz``); the bunch sits near ``pz ≈ 1.7`` MeV/c.
- ``current_Jz_xz.png`` — longitudinal current density ``Jz`` over the ``x``-``z``
  plane, the drive beam's compact current channel that drives the wake. (After
  only 10 steps the cold background plasma is barely perturbed, so its own phase
  space is uninformative; the beam current is the clearer companion to ``Ez``.)

The driver script
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from warpx import WarpX

   w = WarpX(input_file="plasma_acceleration.yaml", path="output", verbose=True)
   w.run()

   w.plot_fields("Ez", "x", "z").savefig("wakefield_Ez_xz.png")
   w.plot2D("z", "pz", species="beam").savefig("phase_space_beam_z_pz.png")
   w.plot_fields("Jz", "x", "z").savefig("current_Jz_xz.png")

Uniform thermal plasma
----------------------

A spatially uniform, hot, collisionless electron plasma, in
``examples/uniform_plasma/``, ported from the WarpX
``inputs_test_2d_uniform_plasma`` reference input — a basic PIC benchmark with
no walls or drives.

- **Uniform hot plasma** — electrons fill the domain at a constant density
  (``1e25`` m⁻³) with an isotropic Gaussian thermal spread of 0.01c per
  component (``rms_velocity``), with an implied neutralizing background.
- **Electromagnetic Yee solver** — second-order Yee FDTD scheme (``EM_Yee``) at
  the Courant limit (``cfl = 1.0``).
- **Doubly-periodic box** — both axes use periodic field and particle
  boundaries, so the plasma should stay statistically uniform.

Running
~~~~~~~

.. code-block:: bash

   cd examples/uniform_plasma
   python run.py

This steps the simulation for 10 steps and writes:

- ``rho_xz.png`` — the charge density ``rho`` over the box; a neutral uniform
  plasma is dominated by small thermal/numerical fluctuations rather than any
  large-scale structure.
- ``phase_space_z_pz.png`` — longitudinal phase space (``z`` vs. ``pz``); the
  thermal electrons fill the box with a Gaussian ``pz`` spread and no net drift.
- ``sigma_x_vs_z.png`` — per-slice transverse extent vs. ``z``; since the
  electrons fill the box uniformly, ``sigma_x`` should be essentially flat.

The driver script
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from warpx import WarpX

   w = WarpX(input_file="uniform_plasma.yaml", path="output", verbose=True)
   w.run()

   w.plot_fields("rho", "x", "z").savefig("rho_xz.png")
   w.plot2D("z", "pz").savefig("phase_space_z_pz.png")
   w.plot1D("z", "sigma_x").savefig("sigma_x_vs_z.png")
