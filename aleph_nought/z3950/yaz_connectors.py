from ctypes import CDLL, POINTER, c_char_p, c_int, c_void_p, cast

from marcdantic import MarcRecord

from .yaz_types import ResultSet

yaz = CDLL("libyaz.so.5")

yaz.ZOOM_connection_new.argtypes = [c_char_p, c_int]
yaz.ZOOM_connection_new.restype = POINTER(c_void_p)

yaz.ZOOM_connection_destroy.argtypes = [POINTER(c_void_p)]
yaz.ZOOM_connection_destroy.restype = None

yaz.ZOOM_connection_option_set.argtypes = [
    POINTER(c_void_p),
    c_char_p,
    c_char_p,
]
yaz.ZOOM_connection_option_set.restype = None


yaz.ZOOM_connection_search_pqf.argtypes = [
    POINTER(c_void_p),
    c_char_p,
]
yaz.ZOOM_connection_search_pqf.restype = POINTER(ResultSet)

yaz.ZOOM_resultset_record.argtypes = [c_void_p, c_int]
yaz.ZOOM_resultset_record.restype = c_void_p

yaz.ZOOM_record_get.argtypes = [c_void_p, c_char_p, POINTER(c_int)]
yaz.ZOOM_record_get.restype = c_char_p


def new_connection(host, port):
    return yaz.ZOOM_connection_new(host.encode("utf-8"), port)


def set_connection_option(connection, option: str, value: str):
    yaz.ZOOM_connection_option_set(
        connection,
        option.encode("utf-8"),
        value.encode("utf-8"),
    )


def destroy_connection(connection):
    yaz.ZOOM_connection_destroy(connection)


def search_pqf(connection, query: str):
    result_set_p = yaz.ZOOM_connection_search_pqf(
        connection, query.encode("utf-8")
    )
    return cast(result_set_p, POINTER(ResultSet))


def get_num_found(result_set_p):
    return result_set_p.contents.size


def get_result_set_record(
    result_set_p,
    index: int,
):
    record = yaz.ZOOM_resultset_record(result_set_p, index)
    length = c_int(0)

    result = yaz.ZOOM_record_get(
        record, "raw".encode("utf-8"), POINTER(c_int)(length)
    )

    if result is None or length.value == 0:
        raise Exception(f"Result set does not contain record at index {index}")

    return MarcRecord(result)
