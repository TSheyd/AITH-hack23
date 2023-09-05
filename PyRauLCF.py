#pythonnet setup
from pythonnet import load
load("coreclr")
import clr
import os
pathDLL = os.getcwd() + "\\RauLowCountsFilter.dll"
clr.AddReference(pathDLL)
from RauLowCountsFilter import RauLCF

import numpy as np
import numpy.typing as npt
from typing import Any
import ctypes
import System
from System import Array, Int32
from System.Runtime.InteropServices import GCHandle, GCHandleType

_MAP_NP_NET = {
    np.dtype('float32'): System.Single,
    np.dtype('float64'): System.Double,
    np.dtype('int8')   : System.SByte,
    np.dtype('int16')  : System.Int16,
    np.dtype('int32')  : System.Int32,
    np.dtype('int64')  : System.Int64,
    np.dtype('uint8')  : System.Byte,
    np.dtype('uint16') : System.UInt16,
    np.dtype('uint32') : System.UInt32,
    np.dtype('uint64') : System.UInt64,
    np.dtype('bool')   : System.Boolean,
}
_MAP_NET_NP = {
    'Single' : np.dtype('float32'),
    'Double' : np.dtype('float64'),
    'SByte'  : np.dtype('int8'),
    'Int16'  : np.dtype('int16'), 
    'Int32'  : np.dtype('int32'),
    'Int64'  : np.dtype('int64'),
    'Byte'   : np.dtype('uint8'),
    'UInt16' : np.dtype('uint16'),
    'UInt32' : np.dtype('uint32'),
    'UInt64' : np.dtype('uint64'),
    'Boolean': np.dtype('bool'),
}

def asNetArray(npArray):
    '''
    Given a `numpy.ndarray` returns a CLR `System.Array`.  See _MAP_NP_NET for 
    the mapping of Numpy dtypes to CLR types.

    Note: `complex64` and `complex128` arrays are converted to `float32` 
    and `float64` arrays respectively with shape [m,n,...] -> [m,n,...,2]
    '''
    dims = npArray.shape
    dtype = npArray.dtype
    # For complex arrays, we must make a view of the array as its corresponding 
    # float type.
    if dtype == np.complex64:
        dtype = np.dtype('float32')
        dims.append(2)
        npArray = npArray.view(np.float32).reshape(dims)
    elif dtype == np.complex128:
        dtype = np.dtype('float64')
        dims.append(2)
        npArray = npArray.view(np.float64).reshape(dims)

    netDims = Array.CreateInstance(Int32, npArray.ndim)
    for I in range(npArray.ndim):
        netDims[I] = Int32(dims[I])
    
    if not npArray.flags.c_contiguous:
        npArray = npArray.copy(order='C')
    assert npArray.flags.c_contiguous

    try:
        netArray = Array.CreateInstance(_MAP_NP_NET[dtype], netDims)
    except KeyError:
        raise NotImplementedError("asNetArray does not yet support dtype {}".format(dtype))

    try: # Memmove 
        destHandle = GCHandle.Alloc(netArray, GCHandleType.Pinned)
        sourcePtr = npArray.__array_interface__['data'][0]
        destPtr = destHandle.AddrOfPinnedObject().ToInt64()
        ctypes.memmove(destPtr, sourcePtr, npArray.nbytes)
    finally:
        if destHandle.IsAllocated: destHandle.Free()
    return netArray

def FindOptimalThreshold(npMatrix: np.ndarray[np.float32, np.shape([Any, Any])], vector: list[str], min: float, max: float, count: int):
    return RauLCF.FindOptimalThreshold(asNetArray(npMatrix), vector, min, max, count)[0];