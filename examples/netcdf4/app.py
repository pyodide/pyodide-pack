import netCDF4 as nc
import numpy as np

dataset = nc.Dataset("memory.nc", "w", diskless=True, persist=False)
dataset.createDimension("x", 3)
var = dataset.createVariable("data", np.float32, ("x",))
var[:] = np.array([1.0, 2.0, 3.0])
print(f"Data: {var[:]}")
dataset.close()
