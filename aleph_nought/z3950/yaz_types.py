from ctypes import Structure
from ctypes import c_char_p, c_int, c_void_p, c_longlong, POINTER


class ResultSet(Structure):
    _fields_ = [
        ("r_sort_spec", c_void_p),
        ("query", c_void_p),
        ("refcount", c_int),
        ("size", c_longlong),
        ("step", c_int),
        ("piggyback", c_int),
        ("setname", c_char_p),
        ("odr", c_void_p),
        ("record_hash", c_void_p),
        ("options", c_void_p),
        ("connection", c_void_p),
        ("databaseNames", POINTER(c_char_p)),
        ("num_databaseNames", c_int),
        ("mutex", c_void_p),
        ("record_wrbuf", c_void_p),
        ("next", c_void_p),
        ("req_facets", c_char_p),
        ("res_facets", c_void_p),
        ("num_res_facets", c_int),
        ("facets_names", c_char_p),
        ("mc_key", c_void_p),
        ("live_set", c_int),
    ]
