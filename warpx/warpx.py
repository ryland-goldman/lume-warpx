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
        raise NotImplementedError

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
