from lume.base import Base
import os
import time
import tempfile
import pywarpx
import scipy.constants
import json
import h5py
import matplotlib.pyplot as plt
import numpy as np
import warnings
import re
import yaml
__all__ = ["WarpX"]

class WarpX(Base):

    class available:
        grid_type = ["Cartesian3DGrid", "Cartesian2DGrid", "Cartesian1DGrid", "CylindricalGrid"]
        solver_type = ["EM_Yee","EM_CKC","EM_Lehe","EM_PSTD","EM_PSATD","EM_GPSTD","EM_DS","EM_ECT","ES_FFT_LF","ES_FFT_EMS","ES_FFT_EP","ES_FFT_Rel","ES_MLMG_LF","ES_MLMG_EMS","ES_MLMG_EP","ES_MLMG_Rel","Hybrid_RK4","Hybrid_RKF45"]
        diagnostics = ["Particle","Field","TimeAveragedField","ElectrostaticField","Reduced","LabFrameParticle","LabFrameField"]
        applied_fields = ["AnalyticInitial","ConstantApplied","AnalyticApplied","FromFile","PlasmaLens","Mirror"]
        laser_pulses = ["Gaussian","Analytic"]
        species_distributions = ["GaussianBunch","Uniform","Analytic","UniformFlux","AnalyticFlux","ParticleList","FromFile"]
        species_layouts = ["Gridded","PseudoRandom"]

        class fields:
            list = ["E","Ex","Ey","Ez","Er","Etheta","Emag",
                    "B","Bx","By","Bz","Br","Btheta","Bmag",
                    "J","Jx","Jy","Jz","Jr","Jtheta","Jmag",
                    "rho","phi"]
            axis = ["x","y","z","r","theta"]

        class plot1D:
            coordinate = ["x","y","z","r","theta","t"]
            statistic = ["mean","sigma","std","min","max","ptp","delta","cov"]
            scalar = ["norm_emit_x","norm_emit_y","norm_emit_4d","charge","n_particle"]

        class plot2D:
            coordinate = ["x","y","z","r","theta","t",
                          "px","py","pz","pr","ptheta",
                          "kinetic_energy","energy","gamma","beta","p","xp","yp","Lz"]

    def __init__(self, input_file=None, *, initial_particles=None, verbose=False, timeout=None, workdir=None, path=None, **kwargs):
        super().__init__(input_file=input_file, initial_particles=initial_particles, verbose=verbose, timeout=timeout)
        
        self._diag_dir = None
        self._outputs = {}
        self._grid = None
        self._solver = None
        self._sim = None
        self._workdir = workdir
        self._path = path

        if not input_file is None:
            with open(input_file, 'r') as f:
                yaml_loader = yaml.SafeLoader
                yaml_loader.add_implicit_resolver(
                    u'tag:yaml.org,2002:float',
                    re.compile(u'''^(?:
                    [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
                    |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
                    |\\.[0-9_]+(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
                    |[-+]?\\.(?:inf|Inf|INF)
                    |\\.(?:nan|NaN|NAN))$''', re.X),
                    list(u'-+0123456789.'))
                self._input = yaml.load(f, Loader=yaml_loader)

    def _validate_inputs(self, req_inputs, inputs=None, loc=""):
        if inputs == None:
            for input in req_inputs:
                if not input in self._input:
                    raise ValueError(f"Required field WarpX.inputs.{input} not specified")
        else:
            for input in req_inputs:
                if not input in inputs:
                    raise ValueError(f"Required field WarpX.inputs.{loc}{input} not specified")

    def configure(self):
        if not self._input:
            self._error = True
            raise ValueError("WarpX.inputs is empty; nothing to configure")

        if self._path is None:
            self._path = self._workdir or tempfile.mkdtemp(prefix="warpx_")
        os.makedirs(self._path, exist_ok=True)

        self._validate_inputs(["grid","solver","simulation"])
        grid_config = self._input["grid"]
        solver_config = self._input["solver"]
        sim_config = self._input["simulation"]
        
        self._build_grid(grid_config)
        self._build_solver(solver_config)
        self._build_sim(sim_config)
        
        if "fields" in self._input:
            for f in self._input["fields"]: self._build_field(f)
        
        if "lasers" in self._input:
            for l in self._input["lasers"]: self._build_laser(l)

        if "species" in self._input:
            for s in self._input["species"]: self._build_species(s)

        if "diagnostics" in self._input:
            for d in self._input["diagnostics"]: self._build_diag(d)

        self._configured = True
        self.vprint(f"WarpX configured; diagnostics saved to {self._path}")

    def _build_grid(self, grid_config):
        self._validate_inputs(["grid_type"], grid_config, "grid.")
        grid_type = grid_config["grid_type"]
        if not grid_type in self.available.grid_type:
            raise ValueError(f"WarpX.input.grid.grid_type is invalid value `{grid_type}`")
        grid_cls = getattr(pywarpx.picmi, grid_type)
        
        grid_params = []
        if grid_type == "Cartesian3DGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nx", "ny", "nz", "xmin", "xmax", "ymin", "ymax", "zmin", "zmax", "bc_xmin", "bc_xmax", "bc_ymin", "bc_ymax", "bc_zmin", "bc_zmax", "moving_window_velocity", "refined_regions", "lower_bound_particles", "upper_bound_particles", "xmin_particles", "xmax_particles", "ymin_particles", "ymax_particles", "zmin_particles", "zmax_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_xmin_particles", "bc_xmax_particles", "bc_ymin_particles", "bc_ymax_particles", "bc_zmin_particles", "bc_zmax_particles", "guard_cells", "pml_cells", "warpx_max_grid_size", "warpx_max_grid_size_x", "warpx_max_grid_size_y", "warpx_max_grid_size_z", "warpx_blocking_factor", "warpx_blocking_factor_x", "warpx_blocking_factor_y", "warpx_blocking_factor_z", "warpx_potential_lo_x", "warpx_potential_hi_x", "warpx_potential_lo_y", "warpx_potential_hi_y", "warpx_potential_lo_z", "warpx_potential_hi_z", "warpx_start_moving_window_step", "warpx_end_moving_window_step", "warpx_boundary_u_th"]
        elif grid_type == "Cartesian2DGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nx", "ny", "xmin", "xmax", "ymin", "ymax", "bc_xmin", "bc_xmax", "bc_ymin", "bc_ymax", "moving_window_velocity", "refined_regions", "lower_bound_particles", "upper_bound_particles", "xmin_particles", "xmax_particles", "ymin_particles", "ymax_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_xmin_particles", "bc_xmax_particles", "bc_ymin_particles", "bc_ymax_particles", "guard_cells", "pml_cells", "warpx_max_grid_size", "warpx_max_grid_size_x", "warpx_max_grid_size_y", "warpx_blocking_factor", "warpx_blocking_factor_x", "warpx_blocking_factor_y", "warpx_potential_lo_x", "warpx_potential_hi_x", "warpx_potential_lo_z", "warpx_potential_hi_z", "warpx_start_moving_window_step", "warpx_end_moving_window_step", "warpx_boundary_u_th"]
        elif grid_type == "Cartesian1DGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nx", "xmin", "xmax", "bc_xmin", "bc_xmax", "moving_window_velocity", "refined_regions", "lower_bound_particles", "upper_bound_particles", "xmin_particles", "xmax_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_xmin_particles", "bc_xmax_particles", "guard_cells", "pml_cells", "warpx_max_grid_size", "warpx_max_grid_size_x", "warpx_blocking_factor", "warpx_blocking_factor_x", "warpx_potential_lo_z", "warpx_potential_hi_z", "warpx_start_moving_window_step", "warpx_end_moving_window_step", "warpx_boundary_u_th"]
        elif grid_type == "CylindricalGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nr", "nz", "n_azimuthal_modes", "rmin", "rmax", "zmin", "zmax", "bc_rmin", "bc_rmax", "bc_zmin", "bc_zmax", "moving_window_velocity", "refined_regions", "rmin_particles", "rmax_particles", "zmin_particles", "zmax_particles", "lower_bound_particles", "upper_bound_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_rmin_particles", "bc_rmax_particles", "bc_zmin_particles", "bc_zmax_particles", "guard_cells", "pml_cells", "warpx_max_grid_size", "warpx_max_grid_size_x", "warpx_max_grid_size_y", "warpx_blocking_factor", "warpx_blocking_factor_x", "warpx_blocking_factor_y", "warpx_potential_lo_r", "warpx_potential_hi_r", "warpx_potential_lo_z", "warpx_potential_hi_z", "warpx_reflect_all_velocities", "warpx_start_moving_window_step", "warpx_end_moving_window_step", "warpx_boundary_u_th"]
        
        for k in grid_config:
            if k not in grid_params:
                if k == "grid_type": continue
                raise ValueError(f"Unknown attribute WarpX.inputs.grid.{k}")

        kwargs = {k: grid_config[k] for k in grid_params if k in grid_config}
        self._grid = grid_cls(**kwargs)

    def _build_solver(self, solver_config):
        self._validate_inputs(["solver_type"], solver_config, "solver.")
        solver_type = solver_config["solver_type"]
        if not solver_type in self.available.solver_type:
            raise ValueError(f"WarpX.input.solver.solver_type is invalid value `{solver_type}`")
        picmi_solvers = {
            "EM_Yee": ["ElectromagneticSolver","Yee"],
            "EM_CKC": ["ElectromagneticSolver","CKC"],
            "EM_Lehe": ["ElectromagneticSolver","Lehe"],
            "EM_PSTD": ["ElectromagneticSolver","PSTD"],
            "EM_PSATD": ["ElectromagneticSolver","PSATD"],
            "EM_GPSTD": ["ElectromagneticSolver","GPSTD"],
            "EM_DS": ["ElectromagneticSolver","DS"],
            "EM_ECT": ["ElectromagneticSolver","ECT"],
            "ES_FFT_LF": ["ElectrostaticSolver","FFT"],
            "ES_FFT_EMS": ["ElectrostaticSolver","FFT"],
            "ES_FFT_EP": ["ElectrostaticSolver","FFT"],
            "ES_FFT_Rel": ["ElectrostaticSolver","FFT"],
            "ES_MLMG_LF": ["ElectrostaticSolver","Multigrid"],
            "ES_MLMG_EMS": ["ElectrostaticSolver","Multigrid"],
            "ES_MLMG_EP": ["ElectrostaticSolver","Multigrid"],
            "ES_MLMG_Rel": ["ElectrostaticSolver","Multigrid"],
            "Hybrid_RK4": ["HybridPICSolver",False],
            "Hybrid_RKF45": ["HybridPICSolver",True],
        }
        solver_cls = getattr(pywarpx.picmi, picmi_solvers[solver_type][0])
        
        solver_params = []
        applied_kwargs = {}
        if picmi_solvers[solver_type][0] == "ElectromagneticSolver":
            applied_kwargs["method"] = picmi_solvers[solver_type][1]
            solver_params = ["stencil_order", "cfl", "source_smoother", "field_smoother", "subcycling", "galilean_velocity", "divE_cleaning", "divB_cleaning", "pml_divE_cleaning", "pml_divB_cleaning", "warpx_pml_ncell", "warpx_periodic_single_box_fft", "warpx_current_correction", "warpx_psatd_update_with_rho", "warpx_psatd_do_time_averaging", "warpx_psatd_JRhom", "warpx_do_pml_in_domain", "warpx_pml_has_particles", "warpx_do_pml_j_damping"]
        if picmi_solvers[solver_type][0] == "ElectrostaticSolver":
            applied_kwargs["method"] = picmi_solvers[solver_type][1]
            if "Rel" in solver_type:
                applied_kwargs["warpx_relativistic"] = True
            if "EMS" in solver_type:
                applied_kwargs["warpx_magnetostatic"] = True
            if "EP" in solver_type:
                applied_kwargs["warpx_effective_potential"] = True
            solver_params = ["required_precision", "maximum_iterations", "warpx_absolute_tolerance", "warpx_self_fields_verbosity", "warpx_magnetostatic_required_precision", "warpx_magnetostatic_absolute_tolerance", "warpx_magnetostatic_max_iters", "warpx_magnetostatic_verbosity", "warpx_effective_potential_factor", "warpx_effective_potential_time_filter_param", "warpx_effective_potential_density_floor", "warpx_cfl", "warpx_dt_update_interval", "warpx_max_dt"]
        if picmi_solvers[solver_type][0] == "HybridPICSolver":
            applied_kwargs["use_rkf45"] = picmi_solvers[solver_type][1]
            solver_params = ["Te", "n0", "gamma", "n_floor", "plasma_resistivity", "plasma_hyper_resistivity", "substeps", "substep_rtol", "substep_atol", "substep_safety", "substep_max_growth", "max_substep_attempts", "holmstrom_vacuum_region", "Jx_external_function", "Jy_external_function", "Jz_external_function", "A_external", "do_external_diva_cleaning"]
            
        for k in solver_config:
            if k not in solver_params:
                if k == "solver_type": continue
                raise ValueError(f"Unknown attribute WarpX.inputs.solver.{k}")

        kwargs = {k: solver_config[k] for k in solver_params if k in solver_config} | applied_kwargs
        self._solver = solver_cls(grid=self._grid, **kwargs)

    def _build_sim(self, sim_config):
        sim_params = ["time_step_size", "max_steps", "max_time", "particle_shape", "gamma_boost", "load_balancing", "warpx_evolve_scheme", "warpx_current_deposition_algo", "warpx_charge_deposition_algo", "warpx_field_gathering_algo", "warpx_particle_pusher_algo", "warpx_use_filter", "warpx_grid_type", "warpx_do_current_centering", "warpx_field_centering_order", "warpx_current_centering_order", "warpx_serialize_initial_conditions", "warpx_random_seed", "warpx_do_dynamic_scheduling", "warpx_roundrobin_sfc", "warpx_load_balance_intervals", "warpx_load_balance_efficiency_ratio_threshold", "warpx_load_balance_with_sfc", "warpx_load_balance_knapsack_factor", "warpx_load_balance_costs_update", "warpx_costs_heuristic_particles_wt", "warpx_costs_heuristic_cells_wt", "warpx_use_fdtd_nci_corr", "warpx_amr_check_input", "warpx_amr_restart", "warpx_amrex_the_arena_is_managed", "warpx_amrex_the_arena_init_size", "warpx_amrex_use_gpu_aware_mpi", "warpx_do_device_synchronize", "warpx_zmax_plasma_to_compute_max_step", "warpx_compute_max_step_from_btd", "warpx_collisions", "warpx_collisions_split_momentum_push", "warpx_embedded_boundary", "warpx_break_signals", "warpx_checkpoint_signals", "warpx_synchronize_velocity", "warpx_numprocs", "warpx_sort_intervals", "warpx_sort_particles_for_deposition", "warpx_sort_idx_type", "warpx_sort_bin_size", "warpx_used_inputs_file", "warpx_reduced_diags_path", "warpx_reduced_diags_extension", "warpx_reduced_diags_intervals", "warpx_reduced_diags_separator", "warpx_reduced_diags_precision", "warpx_self_fields_required_precision", "warpx_self_fields_absolute_tolerance", "warpx_self_fields_max_iters", "warpx_self_fields_verbosity"]
        for k in sim_config:
            if k not in sim_params:
                raise ValueError(f"Unknown attribute WarpX.inputs.simulation.{k}")
        kwargs = {k: sim_config[k] for k in sim_params if k in sim_config}
        self._sim = pywarpx.picmi.Simulation(solver=self._solver, verbose=int(self._verbose), **kwargs)

    def _build_diag(self, diag_config):
        self._validate_inputs(["diagnostic_type"], diag_config, "diagnostics.")
        diag_type = diag_config["diagnostic_type"]
        if not diag_type in self.available.diagnostics:
            raise ValueError(f"WarpX.input.diagnostics.diagnostic_type is invalid value `{diag_type}`")
        
        diag_cls = getattr(pywarpx.picmi, f"{diag_type}Diagnostic")
        applied_kwargs = {}
        if diag_type == "Particle":
            self._validate_inputs(["period"], diag_config, "diagnostics.")
            diag_params = ["period", "species", "data_list", "step_min", "step_max", "parallelio", "name", "warpx_format", "warpx_openpmd_backend", "warpx_openpmd_encoding", "warpx_file_prefix", "warpx_file_min_digits", "warpx_random_fraction", "warpx_uniform_stride", "warpx_plot_filter_function", "warpx_dump_last_timestep", "warpx_verbose"]
        elif diag_type == "Field" or diag_type == "ElectrostaticField":
            self._validate_inputs(["period"], diag_config, "diagnostics.")
            applied_kwargs["grid"] = self._grid
            diag_params = ["period", "data_list", "step_min", "step_max", "number_of_cells", "lower_bound", "upper_bound", "parallelio", "name", "warpx_plot_raw_fields", "warpx_plot_raw_fields_guards", "warpx_plot_finepatch", "warpx_plot_crsepatch", "warpx_format", "warpx_openpmd_backend", "warpx_openpmd_encoding", "warpx_file_prefix", "warpx_file_min_digits", "warpx_dump_rz_modes", "warpx_dump_last_timestep", "warpx_particle_fields_to_plot", "warpx_particle_fields_species", "warpx_verbose"]
        elif diag_type == "TimeAveragedField":
            self._validate_inputs(["period"], diag_config, "diagnostics.")
            applied_kwargs["grid"] = self._grid
            diag_params = ["period", "data_list", "step_min", "step_max", "number_of_cells", "lower_bound", "upper_bound", "parallelio", "name", "warpx_plot_raw_fields", "warpx_plot_raw_fields_guards", "warpx_plot_finepatch", "warpx_plot_crsepatch", "warpx_format", "warpx_openpmd_backend", "warpx_openpmd_encoding", "warpx_file_prefix", "warpx_file_min_digits", "warpx_dump_rz_modes", "warpx_dump_last_timestep", "warpx_particle_fields_to_plot", "warpx_particle_fields_species", "warpx_verbose", "warpx_time_average_mode", "warpx_average_period_steps", "warpx_average_period_time", "warpx_average_start_step"]
        elif diag_type == "Reduced":
            self._validate_inputs(["period","reduced_type"], diag_config, "diagnostics.")
            applied_kwargs["diag_type"] = diag_config["reduced_type"]
            if not "path" in diag_config:
                applied_kwargs["path"] = os.path.join(self._path, "diags") + os.sep
            diag_params = ["name", "period", "path", "extension", "separator", "species", "bin_number", "bin_max", "bin_min", "normalization", "histogram_function", "filter_function", "bin_max_abs", "bin_max_ord", "bin_min_abs", "bin_min_ord", "bin_number_abs", "bin_number_ord", "histogram_function_abs", "histogram_function_ord", "value_function", "weighting_function", "reduction_type", "probe_geometry", "integrate", "do_moving_window_FP", "x_probe", "y_probe", "z_probe", "interp_order", "resolution", "x1_probe", "y1_probe", "z1_probe", "detector_radius", "target_normal_x", "target_normal_y", "target_normal_z", "target_up_x", "target_up_y", "target_up_z"]
        elif diag_type == "LabFrameParticle":
            self._validate_inputs(["num_snapshots","dt_snapshots"], diag_config, "diagnostics.")
            applied_kwargs["grid"] = self._grid
            diag_params = ["num_snapshots", "dt_snapshots", "data_list", "time_start", "species", "parallelio", "name", "warpx_format", "warpx_openpmd_backend", "warpx_openpmd_encoding", "warpx_file_prefix", "warpx_intervals", "warpx_file_min_digits", "warpx_buffer_size", "warpx_verbose"]
        elif diag_type == "LabFrameField":
            self._validate_inputs(["num_snapshots","dt_snapshots"], diag_config, "diagnostics.")
            applied_kwargs["grid"] = self._grid
            diag_params = ["num_snapshots", "dt_snapshots", "data_list", "z_subsampling", "time_start", "parallelio", "name", "warpx_format", "warpx_openpmd_backend", "warpx_openpmd_encoding", "warpx_file_prefix", "warpx_intervals", "warpx_file_min_digits", "warpx_buffer_size", "warpx_lower_bound", "warpx_upper_bound", "warpx_verbose"]

        if not diag_type == "Reduced":
            applied_kwargs["write_dir"] = os.path.join(self._path, "diags")
            if not "warpx_format" in diag_config:
                applied_kwargs["warpx_format"] = "openpmd"
            if not "warpx_openpmd_backend" in diag_config:
                applied_kwargs["warpx_openpmd_backend"] = "h5"

        kwargs = {k: diag_config[k] for k in diag_params if k in diag_config} | applied_kwargs

        if diag_type in ("Particle", "LabFrameParticle") and "species" in kwargs:
            by_name = {s.name: s for s in self._sim.species}
            resolved = []
            for name in kwargs["species"]:
                if name not in by_name:
                    raise ValueError(f"WarpX.inputs.diagnostics.species references unknown species `{name}`; defined species: {sorted(by_name)}")
                resolved.append(by_name[name])
            kwargs["species"] = resolved

        self._sim.add_diagnostic(diag_cls(**kwargs))

    def _build_field(self, field_config):
        self._validate_inputs(["field_type"], field_config, "fields.")
        field_type = field_config["field_type"]
        if not field_type in self.available.applied_fields:
            raise ValueError(f"WarpX.input.fields.field_type is invalid value `{field_type}`")
        picmi_fields = {
            "AnalyticInitial": "AnalyticInitialField",
            "ConstantApplied": "ConstantAppliedField",
            "AnalyticApplied": "AnalyticAppliedField",
            "FromFile": "LoadInitialField",
            "PlasmaLens": "PlasmaLens",
            "Mirror": "Mirror",
        }
        field_cls = getattr(pywarpx.picmi, picmi_fields[field_type])

        field_params = []
        applied_kwargs = {}
        if field_type == "AnalyticInitial":
            field_params = ["Ex_expression", "Ey_expression", "Ez_expression", "Bx_expression", "By_expression", "Bz_expression", "lower_bound", "upper_bound", "warpx_maxlevel_extEMfield_init", "warpx_do_initial_div_cleaning", "warpx_projection_div_cleaner_atol", "warpx_projection_div_cleaner_rtol"]
        elif field_type == "ConstantApplied":
            field_params = ["Ex", "Ey", "Ez", "Bx", "By", "Bz", "lower_bound", "upper_bound"]
        elif field_type == "AnalyticApplied":
            field_params = ["Ex_expression", "Ey_expression", "Ez_expression", "Bx_expression", "By_expression", "Bz_expression", "lower_bound", "upper_bound"]
        elif field_type == "FromFile":
            self._validate_inputs(["path"], field_config, "fields.")
            applied_kwargs["read_fields_from_path"] = field_config["path"]
            field_params = ["load_B", "load_E", "warpx_do_initial_div_cleaning", "warpx_projection_div_cleaner_atol", "warpx_projection_div_cleaner_rtol"]
        elif field_type == "PlasmaLens":
            self._validate_inputs(["period", "starts", "lengths"], field_config, "fields.")
            field_params = ["period", "starts", "lengths", "strengths_E", "strengths_B"]
        elif field_type == "Mirror":
            self._validate_inputs(["depth", "number_of_cells"], field_config, "fields.")
            field_params = ["x_front_location", "y_front_location", "z_front_location", "depth", "number_of_cells"]

        for k in field_config:
            if k not in field_params:
                if k == "field_type": continue
                raise ValueError(f"Unknown attribute WarpX.inputs.fields.{k}")

        kwargs = {k: field_config[k] for k in field_params if k in field_config} | applied_kwargs
        self._sim.add_applied_field(field_cls(**kwargs))

    def _build_laser(self, laser_config):
        pass

    def _build_species(self, species_config):
        self._validate_inputs(["distribution-type","layout"],species_config,"species.")

        distribution = species_config["distribution-type"]
        layout = species_config["layout"]

        if not distribution in self.available.species_distributions:
            raise ValueError(f"WarpX.input.species.distribution-type is invalid value `{distribution}`")
        if not layout in self.available.species_layouts:
            raise ValueError(f"WarpX.input.species.layout is invalid value `{layout}`")
        
        dist_cls = getattr(pywarpx.picmi, f"{distribution}Distribution")

        dist_params = []
        if distribution == "GaussianBunch":
            self._validate_inputs(["n_physical_particles", "rms_bunch_size"], species_config, "species.")
            dist_params = ["n_physical_particles", "rms_bunch_size", "rms_velocity", "centroid_position", "centroid_velocity", "velocity_divergence", "warpx_do_symmetrize", "warpx_symmetrization_order"]
        elif distribution == "Uniform":
            self._validate_inputs(["density"], species_config, "species.")
            dist_params = ["density", "lower_bound", "upper_bound", "rms_velocity", "directed_velocity", "fill_in"]
        elif distribution == "Analytic":
            self._validate_inputs(["density_expression"], species_config, "species.")
            dist_params = ["density_expression", "momentum_expressions", "momentum_spread_expressions", "lower_bound", "upper_bound", "rms_velocity", "directed_velocity", "fill_in", "warpx_density_min", "warpx_density_max", "warpx_momentum_spread_expressions"]
        elif distribution == "UniformFlux":
            self._validate_inputs(["flux", "flux_normal_axis", "surface_flux_position", "flux_direction"], species_config, "species.")
            dist_params = ["flux", "flux_normal_axis", "surface_flux_position", "flux_direction", "lower_bound", "upper_bound", "rms_velocity", "directed_velocity", "flux_tmin", "flux_tmax", "gaussian_flux_momentum_distribution", "warpx_inject_from_embedded_boundary"]
        elif distribution == "AnalyticFlux":
            self._validate_inputs(["flux", "flux_normal_axis", "surface_flux_position", "flux_direction"], species_config, "species.")
            dist_params = ["flux", "flux_normal_axis", "surface_flux_position", "flux_direction", "lower_bound", "upper_bound", "rms_velocity", "directed_velocity", "flux_tmin", "flux_tmax", "gaussian_flux_momentum_distribution", "warpx_inject_from_embedded_boundary"]
        elif distribution == "ParticleList":
            dist_params = ["x", "y", "z", "ux", "uy", "uz", "weight"]
        elif distribution == "FromFile":
            self._validate_inputs(["file_path"], species_config, "species.")
            dist_params = ["file_path"]

        dist_kwargs = {k: species_config[k] for k in dist_params if k in species_config}

        if layout == "Gridded":
            layout_params = ["n_macroparticle_per_cell"]
            layout_kwargs = {k: species_config[k] for k in layout_params if k in species_config}
            layout_cls = pywarpx.picmi.GriddedLayout(grid=self._grid, **layout_kwargs)
        elif layout == "PseudoRandom":
            layout_params = ["n_macroparticles", "n_macroparticles_per_cell", "seed"]
            layout_kwargs = {k: species_config[k] for k in layout_params if k in species_config}
            layout_cls = pywarpx.picmi.PseudoRandomLayout(grid=self._grid, **layout_kwargs)

        species_params = ["particle_type", "name", "charge_state", "charge", "mass", "particle_shape", "density_scale", "method", "warpx_add_int_attributes", "warpx_add_real_attributes", "warpx_do_not_deposit", "warpx_do_not_gather", "warpx_do_not_push", "warpx_do_resampling", "warpx_do_temperature_deposition", "warpx_radial_numpercell_power", "warpx_random_theta", "warpx_reflection_model_eb", "warpx_reflection_model_xhi", "warpx_reflection_model_xlo", "warpx_reflection_model_yhi", "warpx_reflection_model_ylo", "warpx_reflection_model_zhi", "warpx_reflection_model_zlo", "warpx_resampling_algorithm", "warpx_resampling_min_ppc", "warpx_save_particles_at_eb", "warpx_save_particles_at_xhi", "warpx_save_particles_at_xlo", "warpx_save_particles_at_yhi", "warpx_save_particles_at_ylo", "warpx_save_particles_at_zhi", "warpx_save_particles_at_zlo", "warpx_save_previous_position", "warpx_self_fields_max_iters", "warpx_self_fields_verbosity"]

        allowed = set(species_params) | set(dist_params) | set(layout_params) | {"distribution-type", "layout", "initialize_self_field"}
        for k in species_config:
            if k not in allowed:
                raise ValueError(f"Unknown attribute WarpX.inputs.species.{k}")

        kwargs = {k: species_config[k] for k in species_params if k in species_config}
        self._sim.add_species(
            pywarpx.picmi.Species(initial_distribution=dist_cls(**dist_kwargs), **kwargs),
            layout=layout_cls,
            initialize_self_field=species_config["initialize_self_field"] if "initialize_self_field" in species_config else None
        )

    def _build_collisions(self, collison_config):
        pass

    def _build_evolve_scheme(self, es_config):
        pass

    def _build_embedded_boundary(self, eb_config):
        pass

    def _build_smoother(self, smoother_config):
        pass

    def _build_preconditioner(self, pc_config):
        pass

    def run(self):
        if not self._configured:
            self.configure()

        t0 = time.time()
        self.vprint("Running WarpX...")
        try:
            self._sim.step()
            self._finished = True
        except Exception:
            self._error = True
            raise
        finally:
            self.vprint(f"WarpX run took {time.time() - t0:.1f} s")

        self.load_output()

    def archive(self, h5=None):
        if h5 is None:
            h5 = f"warpx_{self.fingerprint()}.h5"
        if isinstance(h5, str):
            h5 = h5py.File(h5, "w")

        h5.attrs["fingerprint"] = self.fingerprint()
        h5.attrs["finished"] = self._finished

        h5.create_group("input").attrs["json"] = json.dumps(self._input)
        g_out = h5.create_group("output")

        if self._outputs:
            if self._diag_dir is None or not os.path.isdir(self._diag_dir):
                raise FileNotFoundError("Cannot archive output: diagnostics directory is unknown or missing. Run load_output() first.")
            iters = sorted({int(i) for ts in self._outputs.values() for i in ts.iterations})
            g_out.attrs["iterations"] = json.dumps(iters)
            g_files = g_out.create_group("files")
            for root, _, files in os.walk(self._diag_dir):
                for name in files:
                    abspath = os.path.join(root, name)
                    relpath = os.path.relpath(abspath, self._diag_dir)
                    with open(abspath, "rb") as f:
                        data = np.frombuffer(f.read(), dtype="uint8")
                    g_files.create_dataset(relpath, data=data)

        self.vprint("Archived WarpX state")
        return h5

    def load_archive(self, h5, configure=True):
        if isinstance(h5, str):
            h5 = h5py.File(h5, "r")

        self._input = json.loads(h5["input"].attrs["json"])
        self._finished = bool(h5.attrs.get("finished", False))
        self._configured = False
        self._error = False
        self._path = tempfile.mkdtemp(prefix="warpx_archive_")

        self._output = None
        self._outputs = {}
        if "output" in h5 and "files" in h5["output"]:
            diags_dir = os.path.join(self._path, "diags")
            g_files = h5["output"]["files"]

            def _restore(name, obj):
                if isinstance(obj, h5py.Dataset):
                    dest = os.path.join(diags_dir, name)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(obj[()].astype("uint8").tobytes())

            g_files.visititems(_restore)
            self.load_output()  # auto-discover every restored series

        if configure: self.configure()
        self.vprint("Loaded WarpX archive")

    def load_output(self, diag_dir=None):
        from openpmd_viewer import OpenPMDTimeSeries

        if diag_dir is not None:
            candidates = {os.path.basename(os.path.normpath(diag_dir)): diag_dir}
        else:
            diags = os.path.join(self._path, "diags")
            if not os.path.isdir(diags):
                raise FileNotFoundError(f"No WarpX diagnostics directory found at {diags}")
            candidates = {name: os.path.join(diags, name) for name in sorted(os.listdir(diags)) if os.path.isdir(os.path.join(diags, name))}

        self._outputs = {}
        for name, sub in candidates.items():
            try:
                self._outputs[name] = OpenPMDTimeSeries(sub)
            except Exception:
                continue

        if not self._outputs:
            raise FileNotFoundError(f"No readable openPMD diagnostics found under {self._path}/diags")

        self._diag_dir = os.path.join(self._path, "diags")
        self._output = next(iter(self._outputs.values()))
        self.vprint(f"Loaded {len(self._outputs)} diagnostic series: {sorted(self._outputs)}")
        return self._outputs

    # TODO: replace the remainder of the file from here with human code (below was generated with Claude Opus 4.8)

    def _validate_output(self):
        if not self._outputs:
            raise RuntimeError("No output loaded; call run() or load_output() first")
        return self._outputs

    def _series_for_species(self, species):
        """Pick the diagnostic series that holds `species` (or the first with any particles)."""
        series = self._validate_output()
        with_particles = {nm: ts for nm, ts in series.items() if ts.avail_species}
        if not with_particles:
            raise ValueError("No particle species in any WarpX diagnostic series")
        if species is None:
            ts = next(iter(with_particles.values()))
            return ts, ts.avail_species[0]
        for ts in with_particles.values():
            if species in (ts.avail_species or []):
                return ts, species
        avail = sorted({s for ts in with_particles.values() for s in (ts.avail_species or [])})
        raise ValueError(f"Unknown species `{species}`; available: {avail}")

    def _validate_coord(self, coord, scope="plot2D"):
        allowed = self.available.plot1D.coordinate if scope == "plot1D" else self.available.plot2D.coordinate
        if coord not in allowed:
            raise ValueError(f"Unknown coordinate `{coord}`; expected one of {allowed}")
        return coord

    def _particle_group(self, species=None, iteration=None, select=None):
        import beamphysics

        ts, species = self._series_for_species(species)

        if iteration is None: iteration = int(ts.iterations[-1])

        want = [c for c in ("x", "y", "z", "ux", "uy", "uz", "w", "mass", "charge") if c in ts.avail_record_components[species]]
        arrays = dict(zip(want, ts.get_particle(want, species=species, iteration=iteration, select=select)))

        n = len(next(iter(arrays.values()))) if arrays else 0
        if n == 0: raise ValueError(f"Species `{species}` has no particles at iteration {iteration}")
        zeros = np.zeros(n)
        x, y, z = (arrays.get(k, zeros) for k in ("x", "y", "z"))
        ux, uy, uz = (arrays.get(k, zeros) for k in ("ux", "uy", "uz"))
        w = arrays.get("w", np.ones(n))

        mass_eV, charge_C = None, None
        if "mass" in arrays:
            m_kg = float(arrays["mass"][0])
            mass_eV = m_kg * scipy.constants.c ** 2 / scipy.constants.e if m_kg != 0 else 0.0
        if "charge" in arrays:
            charge_C = float(arrays["charge"][0])
        if mass_eV is None or charge_C is None:
            try:
                mass_eV = beamphysics.species.mass_of(species) if mass_eV is None else mass_eV
                charge_C = beamphysics.species.charge_of(species) if charge_C is None else charge_C
            except Exception:
                warnings.warn(f"Could not determine mass/charge for species `{species}`; momentum and charge scaling may be wrong")

        if mass_eV is not None and str(species) not in beamphysics.species.MASS_OF:
            beamphysics.species.MASS_OF[str(species)] = mass_eV
        if charge_C is not None and str(species) not in beamphysics.species.CHARGE_OF:
            beamphysics.species.CHARGE_OF[str(species)] = charge_C

        if mass_eV is not None and mass_eV != 0.0:  # massive: openpmd_viewer momenta are gamma*beta
            px, py, pz = ux * mass_eV, uy * mass_eV, uz * mass_eV
        else:        # massless (or unknown mass): momenta are already in kg*m/s
            scale = scipy.constants.c / scipy.constants.e
            px, py, pz = ux * scale, uy * scale, uz * scale

        weight = np.abs(w * charge_C) if charge_C else w
        t_sim = float(ts.t[list(ts.iterations).index(iteration)])
        data = dict(x=x, y=y, z=z, px=px, py=py, pz=pz, t=np.full(n, t_sim), status=np.ones(n), weight=weight, species=str(species))
        return beamphysics.ParticleGroup(data=data)

    def _parse_field(self, field):
        # Search every series that carries fields and return the one holding this field,
        # along with the parsed (name, mode, coord). Returns: (ts, name, mode, coord).
        series = self._validate_output()
        with_fields = {nm: ts for nm, ts in series.items() if ts.avail_fields}
        if not with_fields: raise ValueError("No field data in any WarpX diagnostic series")

        for ts in with_fields.values():
            avail = {a.lower(): a for a in ts.avail_fields}

            def is_vector(name): return ts.fields_metadata[name]["type"] == "vector"

            if field.lower() in avail:
                name = avail[field.lower()]
                # a bare vector name (E/B/J) is treated as its magnitude
                return (ts, name, "mag", None) if is_vector(name) else (ts, name, "scalar", None)

            for suffix in ("mag", "theta", "x", "y", "z", "r", "t"):
                base = field[:-len(suffix)]
                if field.endswith(suffix) and base.lower() in avail:
                    name = avail[base.lower()]
                    if not is_vector(name): raise ValueError(f"Field `{field}` looks like a component of `{name}`, but `{name}` is a scalar field — use it without a component suffix")
                    if suffix == "mag": return ts, name, "mag", None
                    coord = "t" if suffix == "theta" else suffix   # openPMD names the azimuth `t`

                    geom = ts.fields_metadata[name]["geometry"]
                    valid = {"x", "y", "z", "r", "t"} if geom == "thetaMode" else {"x", "y", "z"}
                    if coord not in valid: raise ValueError(f"Field `{field}` (component '{coord}') is not valid for {geom} geometry; valid components: {sorted(valid)}")

                    return ts, name, "component", coord

        present = sorted({a for ts in with_fields.values() for a in ts.avail_fields})
        raise ValueError(f"Unknown field `{field}`; expected one of {self.available.fields.list} (present in output: {present})")

    def _field_plane(self, ts, field, coord, x, y, iteration, theta, m):
        axes = list(ts.fields_metadata[field]["axis_labels"])
        for ax in (x, y):
            if ax not in axes:
                raise ValueError(f"Axis `{ax}` is not available for field `{field}`; plane axes must be among {axes}")
        slice_across = [a for a in axes if a not in (x, y)] or None
        F, info = ts.get_field(field=field, coord=coord, iteration=iteration, slice_across=slice_across, theta=theta, m=m)
        order = list(info.axes.values())
        if order == [y, x]: pass
        elif order == [x, y]: F = F.T
        else: raise ValueError(f"Could not orient field plane (got axes {order}, wanted {[y, x]})")
        return F, getattr(info, x), getattr(info, y)

    def plot_fields(self, field, x, y, *args, iteration=None, theta=0.0, m="all", ax=None, **kwargs):
        ts, name, mode, coord = self._parse_field(field)
        if iteration is None:
            iteration = int(ts.iterations[-1])

        if ax is None:
            _, ax = plt.subplots()

        if mode == "mag":
            geom = ts.fields_metadata[name]["geometry"]
            vec_coords = ["r", "t", "z"] if geom == "thetaMode" else ["x", "y", "z"]
            F = None
            for c in vec_coords:
                Fc, xc, yc = self._field_plane(ts, name, c, x, y, iteration, theta, m)
                F = Fc ** 2 if F is None else F + Fc ** 2
            F = np.sqrt(F)
            label = f"|{name}|"
        else:  # 'component' or 'scalar'
            F, xc, yc = self._field_plane(ts, name, coord, x, y, iteration, theta, m)
            label = field
        extent = [xc[0], xc[-1], yc[0], yc[-1]]
        im = ax.imshow(F, extent=extent, origin="lower", aspect="auto", **kwargs)
        ax.figure.colorbar(im, ax=ax, label=label)

        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(f"{label} (iteration {iteration})")
        self.vprint(f"Plotted field {field} over the {x}-{y} plane at iteration {iteration}")
        return ax.figure

    def plot1D(self, x, y, *args, species=None, iteration=None, select=None, n_slice=50, **kwargs):
        if x not in self.available.plot1D.coordinate:
            raise ValueError(f"Unknown slice coordinate `{x}`; expected one of {self.available.plot1D.coordinate}")
        stat = self._parse_stat(y)

        if x == "t":
            ts, species = self._series_for_species(species)

            times, yvals = [], []
            for it, t in zip(ts.iterations, ts.t):
                try:
                    pg = self._particle_group(species=species, iteration=int(it), select=select)
                except ValueError:
                    continue  # skip dumps with no particles for this species
                times.append(float(t))
                yvals.append(pg[stat])

            fig, ax = plt.subplots()
            ax.plot(times, yvals, **kwargs)
            ax.set_xlabel("t [s]")
            ax.set_ylabel(y)
            ax.set_title(f"{y} vs t")
            self.vprint(f"Plotted {y} vs t over {len(times)} dumps")
            return fig

        pg = self._particle_group(species=species, iteration=iteration, select=select)
        fig = pg.slice_plot(stat, slice_key=x, n_slice=n_slice, return_figure=True, **kwargs)
        self.vprint(f"Plotted {y} vs {x} ({pg.n_particle} particles)")
        return fig

    def _parse_stat(self, y):
        if y in self.available.plot1D.scalar:
            return y
        if y.startswith("cov_"):
            parts = y[len("cov_"):].split("__")
            if len(parts) != 2:
                raise ValueError(f"`cov` statistic must be cov_<a>__<b>, got `{y}`")
            return "cov_" + "__".join(self._validate_coord(p, scope="plot1D") for p in parts)
        for prefix in self.available.plot1D.statistic:
            if prefix == "cov":
                continue
            if y.startswith(prefix + "_"):
                base = y[len(prefix) + 1:]
                prefix = "sigma" if prefix == "std" else prefix
                return f"{prefix}_{self._validate_coord(base, scope='plot1D')}"
        raise ValueError(f"Unknown statistic `{y}`; use <stat>_<coord> with stat in {self.available.plot1D.statistic}, or one of {self.available.plot1D.scalar}")

    def plot2D(self, x, y, *args, species=None, iteration=None, select=None, bins=None, **kwargs):
        kx, ky = self._validate_coord(x), self._validate_coord(y)
        pg = self._particle_group(species=species, iteration=iteration, select=select)
        fig = pg.plot(kx, ky, bins=bins, return_figure=True, **kwargs)
        self.vprint(f"Plotted {y} vs {x} phase space ({pg.n_particle} particles)")
        return fig
