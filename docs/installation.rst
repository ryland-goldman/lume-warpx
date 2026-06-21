Installation
============

LUME-WarpX depends on **WarpX** through its Python bindings, ``pywarpx``.
Because ``pywarpx`` is not distributed on PyPI, you must build or install it
from source first; the rest of the dependencies install normally with ``pip``.

1. Install WarpX / pywarpx
--------------------------

Follow the official WarpX user installation guide:
https://warpx.readthedocs.io/en/latest/install/users.html

The quickest route is usually conda-forge:

.. code-block:: bash

   conda create -n warpx -c conda-forge warpx
   conda activate warpx

2. Install LUME-WarpX
---------------------

``lume-warpx`` is available on PyPi:

.. code-block:: bash

   pip install lume-warpx


Requirements
------------

- Python ≥ 3.10
- ``pywarpx`` installed
- Dependencies: ``lume-base``, ``openpmd``, ``numpy``, ``scipy``, ``h5py``, ``matplotlib``
