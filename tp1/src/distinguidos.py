#!/bin/python3

import argparse
import scapy.all as sc
import sys
import time

from math import log2

WHO_HAS = 1


def nuevo_paquete(fuente_apariciones, total):
# el handler de prn solo puede tener un parametro libre (y por lo tanto no
# deja pasar el diccionario y el total) por eso hay que anidar:
    def contar_paquete(paquete):
        nonlocal fuente_apariciones, total
        if sc.ARP in paquete and paquete[sc.ARP].op == WHO_HAS:
            buscado = paquete[sc.ARP].pdst # es la ip del request
            fuente_apariciones[buscado] = 1 if buscado not in fuente_apariciones else fuente_apariciones[buscado] + 1
            total[0] += 1
            print("Who-has con destino {}".format(buscado))
        return
    return contar_paquete

if __name__ == '__main__':

    fuente_apariciones = {}
    total = [0] # para que sea mutable

    # cargamos pcap o escuchamos por interfaces:
    try:
        if len(sys.argv) > 1:
            path = sys.argv[1]
            try:
                pkts = sc.rdpcap(path)
            except FileNotFoundError as e:
                print(e, file=sys.stderr)
                sys.exit()
            for p in pkts: nuevo_paquete(fuente_apariciones, total)(p)
        else:
            print("Interrumpir con ctrl-C")
            sc.sniff(prn=nuevo_paquete(fuente_apariciones, total), count=0, store=0, filter="arp")

    except KeyboardInterrupt:
            print("Terminó de sniffear")

    total = total[0]
    #  ahora hacemos las cuentitas
    if total == 0:
        print("No se encontraron paquetes ARP del tipo who-has")
        sys.exit()

    print()

    # siempre la proba es mayor a 0 (porque estan en el diccionario)
    fuente_probabilidades = {s: fuente_apariciones[s] / total for s in fuente_apariciones}
    fuente_informacion = {s: -log2(fuente_probabilidades[s]) for s in fuente_probabilidades}

    fuente_entropia = sum(map(lambda s: fuente_probabilidades[s]*fuente_informacion[s], fuente_apariciones))

    for simbolo in fuente_informacion:
        if fuente_entropia > fuente_informacion[simbolo]:
            print("Nodo distinguido {}".format(simbolo))
