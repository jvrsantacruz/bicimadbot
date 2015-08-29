import os
import json


def load_json(path):
    with open(path, 'r') as stream:
        return json.load(stream)


HERE = os.path.abspath(os.path.dirname(__file__))
RESPONSE = load_json(os.path.join(HERE, '../examples/bicimad-response.json'))
N_STATIONS = len(RESPONSE['estaciones'])


FIRST_STATION = {
    "idestacion":"1",
    "nombre":"Puerta del Sol A",
    "numero_estacion":"1a",
    "direccion":"Puerta del Sol No 1",
    "latitud":"40.4168961",
    "longitud":"-3.7024255",
    "activo":"1",
    "luz":"2",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"8",
    "bases_libres":"7",
    "porcentaje":29.166666666667
}


AVAILABLE_STATION = {
    "idestacion":"56",
    "nombre":"Pza.  Santa Ana",
    "numero_estacion":"52",
    "direccion":"Plaza Santa Ana No 10",
    "latitud":"40.4144226",
    "longitud":"-3.7007164",
    "activo":"1",
    "luz":"1",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"13",
    "bases_libres":"5",
    "porcentaje":20.833333333333
}


UNAVAILABLE_STATION = {
    "idestacion":"57",
    "nombre":"Pza.  Lavapies",
    "numero_estacion":"53",
    "direccion":"NO OPERATIVA",
    "latitud":"40.4089282",
    "longitud":"-3.7008803",
    "activo":"1",
    "luz":3,
    "no_disponible":"1",
    "numero_bases":"24",
    "bicis_enganchadas":"0",
    "bases_libres":"0",
    "porcentaje":0
}

NO_ACTIVE_STATION = {
    "idestacion":"3",
    "nombre":"Miguel Moya",
    "numero_estacion":"2",
    "direccion":"Miguel Moya No 1",
    "latitud":"40.4205886",
    "longitud":"-3.7058415",
    "activo":"0",
    "luz":"0",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"0",
    "bases_libres":"15",
    "porcentaje":62.5
}

NO_BIKES_STATION = {
    "idestacion":"11",
    "nombre":"Marques de la Ensenada",
    "numero_estacion":"10",
    "direccion":"Calle Marques de la Ensenada No 16",
    "latitud":"40.4250863",
    "longitud":"-3.6918807",
    "activo":"1",
    "luz":"0",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"0",
    "bases_libres":"24",
    "porcentaje":100
}
