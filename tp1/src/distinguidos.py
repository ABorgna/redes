#!/bin/python3

import argparse
import scapy.all as sc
import sys
import time

from math import log2

WHO_HAS = 1


def nuevo_paquete(fuente, total):
# el handler de prn solo puede tener un parametro libre (y por lo tanto no
# deja pasar el diccionario y el total) por hay que anidar:
    def contar_paquete(paquete):
        nonlocal fuente, total
        if paquete[sc.ARP].op == WHO_HAS:
            buscado = paquete[sc.ARP].pdst
            fuente[buscado] = 1 if buscado not in fuente else fuente[buscado] + 1
            total += 1
    print()
    return contar_paquete

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
            for p in pkts: nuevo_paquete(fuente, total)(p)
        else:
            print("Interrumpir con ctrl-C")
            sc.sniff(prn=nuevo_paquete(fuente, total), count=0, store=0, filter="arp")

    except KeyboardInterrupt:
            print("Terminó de sniffear")

    # TODO ahora hacemos las cuentitas:
    # TODO definir noción de distinguido
