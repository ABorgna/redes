#!/usr/bin/python3
import base64
import requests
import shutil
import sys
import urllib

import traceroute

GEOIP_ENDPOINT = "http://freegeoip.net/json/"
STATICMAPS_ENDPOIND = "https://maps.googleapis.com/maps/api/staticmap"

# At least it's not plain text
MAPS_ENC_KEY = b'QUl6YVN5QkFoX0pLWmtRNGVjN0trdlJoM1A2UzMzWFdZN29xeXZV'
MAPS_KEY = base64.b64decode(MAPS_ENC_KEY).decode('utf-8')

def ip_info(ip):
    ''' Devuelve un diccionario con
        ip, country_code, country_name, region_code, city,
        zip_code, time_zone, latitude, longitude, metro_code
    '''
    url = GEOIP_ENDPOINT + str(ip)
    r = requests.get(url)

    if r.status_code != 200:
        raise IOError("Hubo un problema con la conexion a freegeoip")

    return r.json()

def ip_coords(ip):
    info = ip_info(ip)
    return (info["latitude"], info["longitude"])

def generate_route_map(imgfile, ips, times=None):
    points = map(ip_info, ips)

    # Generate the path data
    path_style = [
            "color: blue",
            "geodesic:true", # Follow earth's curvature
            "weight:2",
    ]
    path_points = [str(p["latitude"]) + "," + str(p["longitude"])
                   for p in points if p["latitude"] != 0]
    path_query = "|".join(path_style + path_points)

    # Build the url query
    query = [
            # Output params
            ("key", MAPS_KEY),
            #("zoom", 1), # World level
            ("size", "640x640"),
            # Style params
            ("style", "element:labels|visibility:off"),
            ("style", "feature:administrative.land_parcel|visibility:off"),
            ("style", "feature:administrative.neighborhood|visibility:off"),
            ("style", "feature:poi.business|visibility:off"),
            ("style", "feature:road|visibility:off"),
            ("style", "feature:road|element:labels.icon|visibility:off"),
            ("style", "feature:transit|visibility:off"),
            # Path
            ("path", path_query)
    ]

    querystring = urllib.parse.urlencode(query)
    url = STATICMAPS_ENDPOIND + "?" + querystring

    # Make the request
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        raise IOError("Hubo un problema con la conexion a google maps")

    with open(imgfile, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Genera una imagen gráfica de un traceroute", file=sys.stderr)
        print("Uso:", sys.argv[0], "IP", "IMAGE_FILE", file=sys.stderr)
    else:
        target = sys.argv[1]
        imgfile = sys.argv[2]

        # 1 iteracion para que no tarde años
        times = traceroute.armar_rutas(target, 1)
        ips = []
        tiempos = []
        for ttl, tanda in times.items():
            if tanda:
                ip, tiempo = tanda[0]
                ips.append(ip)
                tiempos.append(tiempo)

        generate_route_map(imgfile, ips, tiempos)

