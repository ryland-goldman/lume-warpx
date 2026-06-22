Configuration (YAML input)
==========================

.. note::

   See descriptions of input parameters in the `WarpX PICMI documentation <https://warpx.readthedocs.io/en/latest/usage/python.html>`_

A simulation is defined by a single YAML file passed as ``input_file``. The
top level is a mapping with these sections:

==================  ========  =================================================
Section             Required  Purpose
==================  ========  =================================================
``grid``            yes       Geometry, resolution, and boundary conditions
``solver``          yes       Field solver (electromagnetic / -static / hybrid)
``simulation``      yes       Time stepping and global algorithm options
``fields``          no        Applied / initial fields (list)
``lasers``          no        Laser pulses (list) — *not yet implemented*
``species``         no        Particle species (list)
``diagnostics``     no        Output diagnostics (list)
==================  ========  =================================================

Each section's keys map directly onto the corresponding
`PICMI <https://picmi-standard.github.io/>`_ object. Every value listed by that
PICMI class is accepted, including the ``warpx_*`` backend options; an unknown
key raises a ``ValueError`` that names the offending field. The accepted value
lists are also enumerated on :class:`warpx.warpx.WarpX.available`.

grid
----

``grid_type`` selects the geometry; the remaining keys are forwarded to the
matching PICMI grid class.

Valid ``grid_type`` values:

- ``Cartesian3DGrid``
- ``Cartesian2DGrid``
- ``Cartesian1DGrid``
- ``CylindricalGrid``

.. code-block:: yaml

   grid:
     grid_type: Cartesian2DGrid
     number_of_cells: [64, 128]
     lower_bound: [-0.01, 0.0]
     upper_bound: [0.01, 0.02]
     lower_boundary_conditions: [dirichlet, dirichlet]
     upper_boundary_conditions: [dirichlet, dirichlet]
     lower_boundary_conditions_particles: [absorbing, absorbing]
     upper_boundary_conditions_particles: [absorbing, absorbing]
     warpx_potential_lo_z: 0.0
     warpx_potential_hi_z: 150.0e3

Common keys include ``number_of_cells``, ``lower_bound`` / ``upper_bound``,
``lower_boundary_conditions`` / ``upper_boundary_conditions`` (and the
``_particles`` variants), electrode potentials (``warpx_potential_lo_*`` /
``warpx_potential_hi_*``), ``warpx_max_grid_size``, and ``warpx_blocking_factor``.
Cylindrical grids additionally take ``nr``, ``nz``, and ``n_azimuthal_modes``.

solver
------

``solver_type`` selects both the PICMI solver class and its method:

==========================================  ============================
``solver_type``                             Maps to
==========================================  ============================
``EM_Yee`` ``EM_CKC`` ``EM_Lehe``           Electromagnetic (FDTD)
``EM_PSTD`` ``EM_PSATD`` ``EM_GPSTD``        Electromagnetic (spectral)
``EM_DS`` ``EM_ECT``                         Electromagnetic
``ES_FFT_LF`` ``ES_FFT_EMS``                Electrostatic (FFT)
``ES_FFT_EP`` ``ES_FFT_Rel``                Electrostatic (FFT)
``ES_MLMG_LF`` ``ES_MLMG_EMS``              Electrostatic (Multigrid)
``ES_MLMG_EP`` ``ES_MLMG_Rel``              Electrostatic (Multigrid)
``Hybrid_RK4`` ``Hybrid_RKF45``             Hybrid PIC
==========================================  ============================

The electrostatic suffixes pick the physics model automatically:

- ``LF`` — labframe (standard)
- ``EMS`` — labframe **electromagnetostatic** (adds a magnetostatic solve)
- ``EP`` — labframe **effective potential**
- ``Rel`` — **relativistic** electrostatic

.. code-block:: yaml

   solver:
     solver_type: ES_MLMG_EMS
     required_precision: 1.0e-6
     warpx_magnetostatic_required_precision: 1.0e-6
     warpx_self_fields_verbosity: 0

Electromagnetic solvers accept ``cfl``, ``stencil_order``, and PML options;
electrostatic solvers accept ``required_precision``, ``maximum_iterations``,
and the ``warpx_magnetostatic_*`` / ``warpx_effective_potential_*`` options;
hybrid solvers accept ``Te``, ``n0``, ``plasma_resistivity``, and substep
controls.

simulation
----------

Time stepping and global algorithm selection. No ``*_type`` key — the keys map
directly onto :class:`pywarpx.picmi.Simulation`.

.. code-block:: yaml

   simulation:
     time_step_size: 1.0e-12
     max_time: 3.0e-10
     particle_shape: 1

Frequently used keys: ``time_step_size``, ``max_steps``, ``max_time``,
``particle_shape``, ``gamma_boost``, and the many ``warpx_*`` algorithm options
(deposition, gathering, pusher, load balancing, sorting, embedded boundary,
collisions, …). Verbosity is taken from the constructor's ``verbose`` flag.

fields
------

A list of applied or initial fields. ``field_type`` selects the kind:

=====================  ============================================
``field_type``         Description
=====================  ============================================
``AnalyticInitial``    Initial E/B from analytic expressions
``ConstantApplied``    Constant applied E/B
``AnalyticApplied``    Applied E/B from analytic expressions
``FromFile``           Load **initial** field from a file (``path``)
``AppliedFromFile``    Load a tabulated **applied** (per-step, particle-gathered) field
                       from a file (``path``, ``load_E``/``load_B``,
                       ``warpx_E_time_function``/``warpx_B_time_function``)
``PlasmaLens``         Plasma-lens array (``starts``/``lengths``)
``Mirror``             Field mirror
=====================  ============================================

``AppliedFromFile`` maps to ``picmi.LoadAppliedField``: a tabulated map gathered onto
particles every step, optionally scaled by an AMReX parser ``t``-expression (e.g. an RF
``cos(omega*t + phi)`` standing wave, or a constant solenoid current).

.. code-block:: yaml

   fields:
     - field_type: AppliedFromFile
       path: fields/rf1.h5
       load_E: true
       load_B: true
       warpx_E_time_function: "1.0e5*cos(1.79e10*t + 0.3)"
       warpx_B_time_function: "1.0e5*sin(1.79e10*t + 0.3)"

.. code-block:: yaml

   fields:
     - field_type: ConstantApplied
       Bz: 0.5
     - field_type: AnalyticApplied
       Ez_expression: "1e5 * sin(z)"

species
-------

A list of particle species. Each entry requires a ``distribution-type`` and a
``layout``; the remaining keys configure the species, its initial distribution,
and its particle layout.

Distributions (``distribution-type``):

- ``GaussianBunch`` — needs ``n_physical_particles``, ``rms_bunch_size``
- ``Uniform`` — needs ``density``
- ``Analytic`` — needs ``density_expression``
- ``UniformFlux`` / ``AnalyticFlux`` — surface emission; need ``flux``,
  ``flux_normal_axis``, ``surface_flux_position``, ``flux_direction``
- ``ParticleList`` — explicit ``x``/``y``/``z``/``ux``/``uy``/``uz``/``weight``
- ``FromInitialParticles`` — inject the ``WarpX(initial_particles=...)``
  ``ParticleGroup`` as an explicit ``ParticleList`` (the standard way to seed a beam
  imported from an upstream stage); optional ``n_seed`` keeps only the first *N*
  macroparticles (the rest added later by a ``beforestep`` callback)
- ``FromFile`` — needs ``file_path``

Layouts (``layout``):

- ``Gridded`` — ``n_macroparticle_per_cell``
- ``PseudoRandom`` — ``n_macroparticles`` / ``n_macroparticles_per_cell`` /
  ``seed`` (required for flux injection)

.. code-block:: yaml

   species:
     - particle_type: electron
       name: electron
       distribution-type: UniformFlux
       flux: 6.241509e23
       flux_normal_axis: z
       surface_flux_position: 0.0
       flux_direction: 1
       flux_tmin: 0.0
       flux_tmax: 2.0e-11
       gaussian_flux_momentum_distribution: true
       rms_velocity: [1.5e5, 1.5e5, 1.5e5]
       layout: PseudoRandom
       n_macroparticles_per_cell: 4
       initialize_self_field: false

.. tip::

   Use a standard species ``name`` (e.g. ``electron``) so openPMD-beamphysics
   can resolve the particle mass/charge for energy and kinetic-energy plots.

diagnostics
-----------

A list of output diagnostics. ``diagnostic_type`` selects the kind:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - ``diagnostic_type``
     - Required keys
     - Notes
   * - ``Particle``
     - ``period``
     - Per-species particle dumps
   * - ``Field``
     - ``period``
     - Field grids (``data_list``)
   * - ``TimeAveragedField``
     - ``period``
     - Time-averaged fields
   * - ``ElectrostaticField``
     - ``period``
     - Electrostatic field grids
   * - ``Reduced``
     - ``period``, ``reduced_type``
     - Reduced (scalar) diagnostics
   * - ``LabFrameParticle``
     - ``num_snapshots``, ``dt_snapshots``
     - Back-transformed particles
   * - ``LabFrameField``
     - ``num_snapshots``, ``dt_snapshots``
     - Back-transformed fields

.. code-block:: yaml

   diagnostics:
     - diagnostic_type: Particle
       name: diag1
       period: 30
       species: [electron]
     - diagnostic_type: Field
       name: diag_fields
       period: 30
       data_list: [phi, rho, Ex, Ez]

.. important::

   Unless you override them, non-reduced diagnostics default to
   ``warpx_format: openpmd`` with the ``h5`` backend and are written to
   ``<path>/diags`` (or an explicit ``write_dir`` if given). This is what the
   plotting and archiving helpers expect. For a ``Particle`` / ``LabFrameParticle``
   diagnostic, the ``species`` list must reference species names you defined above.

Runtime overrides and callbacks
-------------------------------

A static YAML config can be patched before :meth:`configure` so a driver can compute
values at run time (RF time-function strings, ``max_steps``, diagnostic periods) and read
constants back instead of duplicating them:

- ``w.get("grid/number_of_cells")`` — read a value by ``/``-separated path (list steps use
  integer indices); returns ``default`` if the path is missing.
- ``w.set("simulation/max_steps", 5000)`` / ``w.update({path: value, ...})`` — override.
- ``w.install_callback("beforestep", fn)`` — register a pywarpx step callback installed for
  the duration of :meth:`run` (e.g. time-release particle injection).
- ``w.run(progress="label", log_path=...)`` — drive the run with a tqdm bar, redirecting
  WarpX's per-step stdout to ``log_path`` (or ``$PIPELINE_LOG_PATH``).
