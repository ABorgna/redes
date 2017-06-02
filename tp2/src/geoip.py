#!/usr/bin/python3
import base64
import math
import requests
import shutil
import sys
import urllib

import traceroute

STATICMAPS_ENDPOIND = "https://maps.googleapis.com/maps/api/staticmap"

# At least it's not plain text
MAPS_ENC_KEY = b'QUl6YVN5QkFoX0pLWmtRNGVjN0trdlJoM1A2UzMzWFdZN29xeXZV'
MAPS_KEY = base64.b64decode(MAPS_ENC_KEY).decode('utf-8')

class Geoip:

    FREEGEOIP_ENDPOINT = "http://freegeoip.net/json/"
    NEKUDO_ENDPOINT = "http://geoip.nekudo.com/api/"

    def coords(ip):
        info = Geoip.info(ip)
        return (info["latitude"], info["longitude"])

    def info(ip):
        ''' Devuelve un diccionario con
            ip, country, city, latitude, longitude
        '''
        providers = [Geoip._get_nekudo, Geoip._get_freegeoip]

        res = None
        for f in providers:
            res = f(ip)
            if res is not None:
                break

        if res is None:
            raise IOError("No se pudo geolocalizar la ip", ip)

        return res

    def _get_freegeoip(ip):
        url = Geoip.FREEGEOIP_ENDPOINT + str(ip)
        r = requests.get(url)

        if r.status_code != 200:
            return None
        j = r.json()

        return {
            "ip": j["ip"],
            "country": j["country_name"],
            "city": j["city"],
            "latitude": j["latitude"],
            "longitude": j["longitude"],
        }

    def _get_nekudo(ip):
        url = Geoip.NEKUDO_ENDPOINT + str(ip)
        r = requests.get(url)

        if r.status_code != 200:
            return None

        j = r.json()
        if "type" in j and j["type"] == "error":
            return None

        return {
            "ip": j["ip"],
            "country": j["country"]["name"],
            "city": j["city"],
            "latitude": j["location"]["latitude"],
            "longitude": j["location"]["longitude"],
        }

class Mapper:

    STYLE_SIMPLE = [
            ("style", "element:labels|visibility:off"),
            ("style", "feature:administrative.land_parcel|visibility:off"),
            ("style", "feature:administrative.neighborhood|visibility:off"),
            ("style", "feature:poi.business|visibility:off"),
            ("style", "feature:road|visibility:off"),
            ("style", "feature:road|element:labels.icon|visibility:off"),
            ("style", "feature:transit|visibility:off"),
    ]

    STYLE_WHITE = [
            ("style", "element:geometry|color:0xf5f5f5"),
            ("style", "element:labels|visibility:off"),
            ("style", "element:labels.icon|visibility:off"),
            ("style", "element:labels.text.fill|color:0x616161"),
            ("style", "element:labels.text.stroke|color:0xf5f5f5"),
            ("style", "feature:administrative.country|element:geometry.stroke|color:0xffffff|visibility:on"),
            ("style", "feature:administrative.land_parcel|visibility:off"),
            ("style", "feature:administrative.land_parcel|element:labels.text.fill|color:0xbdbdbd"),
            ("style", "feature:administrative.neighborhood|visibility:off"),
            ("style", "feature:administrative.province|visibility:off"),
            ("style", "feature:landscape.man_made|visibility:off"),
            ("style", "feature:landscape.natural|element:geometry.fill|color:0xc9c9c9"),
            ("style", "feature:landscape.natural.landcover|element:geometry.fill|color:0xc9c9c9"),
            ("style", "feature:landscape.natural.terrain|element:geometry.fill|color:0xd1d1d1"),
            ("style", "feature:poi|element:geometry|color:0xeeeeee"),
            ("style", "feature:poi|element:labels.text.fill|color:0x757575"),
            ("style", "feature:poi.business|visibility:off"),
            ("style", "feature:poi.park|element:geometry|color:0xe5e5e5"),
            ("style", "feature:poi.park|element:labels.text|visibility:off"),
            ("style", "feature:poi.park|element:labels.text.fill|color:0x9e9e9e"),
            ("style", "feature:road|visibility:off"),
            ("style", "feature:road|element:geometry|color:0xffffff"),
            ("style", "feature:road.arterial|element:labels.text.fill|color:0x757575"),
            ("style", "feature:road.highway|element:geometry|color:0xdadada"),
            ("style", "feature:road.highway|element:labels.text.fill|color:0x616161"),
            ("style", "feature:road.local|element:labels.text.fill|color:0x9e9e9e"),
            ("style", "feature:transit.line|element:geometry|color:0xe5e5e5"),
            ("style", "feature:transit.station|element:geometry|color:0xeeeeee"),
            ("style", "feature:water|element:geometry|color:0xc9c9c9"),
            ("style", "feature:water|element:geometry.fill|color:0xffffff"),
            ("style", "feature:water|element:labels.text.fill|color:0x9e9e9e"),
    ]

    def generate_route_map(imgfile, ips, times=None):
        # Checks
        if times is not None and len(ips) != len(times):
            raise ValueError("ips and times must have the same length")

        # Generate the path data
        path_query = Mapper._get_path_query(ips, times)
        if path_query is None:
            return

        # Build the url query
        query = [
                # Output params
                ("key", MAPS_KEY),
                #("zoom", 1), # World level
                ("size", "640x640"), # Max
        ] + Mapper.STYLE_WHITE + path_query

        querystring = urllib.parse.urlencode(query)
        url = STATICMAPS_ENDPOIND + "?" + querystring

        # Make the request
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            raise IOError("Hubo un problema con la conexion a google maps")

        with open(imgfile, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    def _get_path_query(ips, times):
        path_style = [
                "geodesic:true", # Follow earth's curvature
                "weight:8",
        ]
        path_query = []

        points = [Geoip.info(ip) for ip in ips]

        # Borramos los puntos que no se geolocalizaron (ips privadas)
        if times is not None:
            for i in range(len(points)-1, -1, -1):
                if points[i]["latitude"] == 0:
                    del times[i]
        points = [p for p in points if p["latitude"] != 0]

        if not len(points):
            print("No se pudo geolocalizar ninguna ip", file=sys.stderr)
            return None

        if times is None:
            # Un solo camino del mismo color
            path_points = [str(p["latitude"]) + "," + str(p["longitude"])
                           for p in points if p["latitude"] != 0]
            path_params = "|".join(path_style + path_points)

            path_query.append(("path", path_params))
        else:
            # El color varía según el delay del segmento
            colors = Mapper._get_path_colors(times)

            last = points[0]
            for i in range(len(points)-1):
                u, v = points[i], points[i+1]
                color = colors[i]

                path_points = [str(p["latitude"]) + "," + str(p["longitude"])
                        for p in (u,v)]
                path_color = ["color:" + color]
                path_params = "|".join(path_style + path_color + path_points)

                path_query.append(("path", path_params))

        return path_query

    def _get_path_colors(times):
        deltas = [t2 - t1 for t1, t2 in zip(times, times[1:])]
        dmax = max(deltas)
        dmin = min(d for d in deltas if d > 0)

        logs = [math.log(d) if d > 0 else math.log(dmin) for d in deltas]
        lmax = math.log(dmax)
        lmin = math.log(dmin)

        if lmin == lmax:
            return ["0x7f7f7f" for l in logs]

        # From blue to red
        gradient = Mapper._rgb_gradient((0.5,0.5,0.5), (1,0,0), 128)

        colors = []
        for l in logs:
            index = round(127 * (l - lmin) / (lmax-lmin))
            index = min(max(0,index), 127)
            color = Mapper._rgb_tohex(gradient[index])+"c0"
            colors.append(color)

        return colors

    def _rgb_gradient(start, finish, n=128):
        ''' returns a gradient list of n colors between two rgb colors
        '''
        res = [start]

        # Calculate a color at each evenly spaced value of t from 1 to n
        for t in range(1, n):
            curr_vector = [
              start[j] + (float(t)/(n-1))*(finish[j]-start[j])
              for j in range(3)
            ]
            res.append(curr_vector)

        return res

    def _rgb_tohex(rgb):
        ''' [1,1,1] -> "0xFFFFFF"
        '''
        rgb = [int(x*255) for x in rgb]
        return "0x"+"".join(["{:02x}".format(x) for x in rgb])

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
        for ttl, tanda in times:
            if tanda:
                ip, tiempo = tanda[0]
                ips.append(ip)
                tiempos.append(tiempo)
                print(ip + ":", str(tiempo) + "ms")

        Mapper.generate_route_map(imgfile, ips, tiempos)
