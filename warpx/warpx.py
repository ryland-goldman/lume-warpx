from lume.base import Base
__all__ = ["WarpX"]

class WarpX(Base):
    def configure(self):
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
