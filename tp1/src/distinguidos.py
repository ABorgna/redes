#!/bin/python3

import argparse
import scapy.all as sc
import sys
import time

from math import log2

WHO_HAS = 1


def distinguir(fuente, total):
# el handler de prn solo puede tener un parametro libre (y por lo tanto no
# deja pasar el diccionario y el total) por hay que anidar:
    def nuevo_paquete(paquete):
        if paquete[ARP].op == WHO_HAS:
            buscado = paquete[ARP].pdst
            fuente[buscado] = 1 if buscando not in fuente else fuente[buscado] + 1
            total += 1
    print()
    return nuevo_paquete



if __name__ == '__main__':

    fuente = {}
    total = 0

    # cargamos pcap o escuchamos por interfaces:

    try:
        if len(sys.argv) > 1:
            try:
                pkts = sc.rdpcap(path)
            except FileNotFoundError as e:
                print(e, file=sys.stderr)
                sys.exit()
            for p in pkts: distinguir(fuente, total)(p)
        else:
            print("Interrumpir con ctrl-C")
            sc.sniff(prn=distinguir(fuente, total), store=0, filter="arp")

    except KeyboardInterrupt:
            print("Terminó de sniffear")

    # TODO ahora hacemos las cuentitas:
    # TODO definir noción de distinguido
