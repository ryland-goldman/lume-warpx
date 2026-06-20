from lume.base import Base
import os
import time
import tempfile
import pywarpx
__all__ = ["WarpX"]

class WarpX(Base):
    _grid = None
    _solver = None
    _sim = None

    class available:
        grid_type = ["Cartesian3DGrid", "Cartesian2DGrid", "Cartesian1DGrid", "CylindricalGrid"]
        solver_type = ["EM_Yee","EM_CKC","EM_Lehe","EM_PSTD","EM_PSATD","EM_GPSTD","EM_DS","EM_ECT","ES_FFT_LF","ES_FFT_EMS","ES_FFT_EP","ES_FFT_Rel","ES_MLMG_LF","ES_MLMG_EMS","ES_MLMG_EP","ES_MLMG_Rel","Hybrid_RK4","Hybrid_RKF45"]

    def _validate_inputs(self, req_inputs, inputs=None, loc=""):
        if inputs == None:
            for input in req_inputs:
                if not input in self.inputs:
                    raise ValueError(f"Required field WarpX.inputs.{input} not specified")
        else:
            for input in req_inputs:
                if not input in inputs:
                    raise ValueError(f"Required field WarpX.inputs.{loc}{input} not specified")

    def configure(self):
        if not self.inputs:
            self.error = True
            raise ValueError("WarpX.inputs is empty; nothing to configure")

        if self.path is None:
            self.path = self.workdir or tempfile.mkdtemp(prefix="warpx_")
        os.makedirs(self.path, exist_ok=True)

        self._validate_inputs(["grid","solver","simulation"])
        grid_config = self.inputs["grid"]
        solver_config = self.inputs["solver"]
        sim_config = self.inputs["simulation"]
        
        self._build_grid(grid_config)
        self._build_solver(solver_config)
        self._build_sim(sim_config)

        self.configured = True
        self.vprint(f"WarpX configured; diagnostics saved to {self.path}")

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
        self._sim = pywarpx.picmi.Simulation(solver=self._solver, verbose=int(self.verbose), **kwargs)
    
    def run(self):
        if not self.configured:
            self.configure()

        t0 = time.time()
        self.vprint("Running WarpX...")
        try:
            self._sim.step()
            self.finished = True
        except Exception:
            self.error = True
            raise
        finally:
            self.vprint(f"WarpX run took {time.time() - t0:.1f} s")

        self.load_output()
        raise NotImplementedError

    def archive(self, h5=None):
        raise NotImplementedError

    def load_archive(self, h5, configure=True):
        raise NotImplementedError

    def load_output(self, **kwargs):
        raise NotImplementedError

    def plot(self, *args, **kwargs):
        raise NotImplementedError
