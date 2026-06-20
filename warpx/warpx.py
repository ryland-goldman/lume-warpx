from lume.base import Base
import os
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

        self._validate_inputs(["grid","solver"])
        grid_config = self.input["grid"]
        solver_config = self.input["solver"]

        self._validate_inputs(["solver_type"], solver_config, "solver.")

        
        if not solver_config["solver_type"] in self.available.solver_type:
            raise ValueError(f"WarpX.inputs.solver.solver_type is invalid value `{solver_config["solver_type"]}`")
        
        self._build_grid(grid_config)
        self._build_solver(solver_config)

        self._sim = pywarpx.picmi.Simulation(
            solver=self._solver,
            max_steps=self.input["max_steps"],
            verbose=int(self.verbose),
        )

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
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nx", "ny", "nz", "xmin", "xmax", "ymin", "ymax", "zmin", "zmax", "bc_xmin", "bc_xmax", "bc_ymin", "bc_ymax", "bc_zmin", "bc_zmax", "moving_window_velocity", "refined_regions", "lower_bound_particles", "upper_bound_particles", "xmin_particles", "xmax_particles", "ymin_particles", "ymax_particles", "zmin_particles", "zmax_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_xmin_particles", "bc_xmax_particles", "bc_ymin_particles", "bc_ymax_particles", "bc_zmin_particles", "bc_zmax_particles", "guard_cells", "pml_cells"]
        elif grid_type == "Cartesian2DGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nx", "ny", "xmin", "xmax", "ymin", "ymax", "bc_xmin", "bc_xmax", "bc_ymin", "bc_ymax", "moving_window_velocity", "refined_regions", "lower_bound_particles", "upper_bound_particles", "xmin_particles", "xmax_particles", "ymin_particles", "ymax_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_xmin_particles", "bc_xmax_particles", "bc_ymin_particles", "bc_ymax_particles", "guard_cells", "pml_cells"]
        elif grid_type == "Cartesian1DGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nx", "xmin", "xmax", "bc_xmin", "bc_xmax", "moving_window_velocity", "refined_regions", "lower_bound_particles", "upper_bound_particles", "xmin_particles", "xmax_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_xmin_particles", "bc_xmax_particles", "guard_cells", "pml_cells"]
        elif grid_type == "CylindricalGrid":
            grid_params = ["number_of_cells", "lower_bound", "upper_bound", "lower_boundary_conditions", "upper_boundary_conditions", "nr", "nz", "n_azimuthal_modes", "rmin", "rmax", "zmin", "zmax", "bc_rmin", "bc_rmax", "bc_zmin", "bc_zmax", "moving_window_velocity", "refined_regions", "rmin_particles", "rmax_particles", "zmin_particles", "zmax_particles", "lower_bound_particles", "upper_bound_particles", "lower_boundary_conditions_particles", "upper_boundary_conditions_particles", "bc_rmin_particles", "bc_rmax_particles", "bc_zmin_particles", "bc_zmax_particles", "guard_cells", "pml_cells"]
        
        for k in grid_config:
            if k not in grid_params:
                if k == "grid_type": continue
                raise ValueError(f"Unknown attribute WarpX.inputs.grid.{k}")

        kwargs = {k: grid_config[k] for k in grid_params if k in grid_config}
        self._grid = grid_cls(**kwargs)

    def _build_solver(self, solver_config):
        raise NotImplementedError
    
    def run(self):
        raise NotImplementedError

    def archive(self, h5=None):
        raise NotImplementedError

    def load_archive(self, h5, configure=True):
        raise NotImplementedError

    def load_output(self, **kwargs):
        raise NotImplementedError

    def plot(self, *args, **kwargs):
        raise NotImplementedError
