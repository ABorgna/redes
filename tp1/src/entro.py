#!/bin/python3

import argparse
import scapy.all as sc
import sys
import time

from math import log2
from typing import List

def readFromFile(path):
    try:
        pkts = sc.rdpcap(path)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return

    broadcast, unicast = getCounts(pkts)

    printEntropy(broadcast, unicast)

    print()

sniffedGlobals = {}
def readFromIF(interface=None):
    PRINT_TIMEOUT = 0.2

    sniffedGlobals['broadcast'] = 0
    sniffedGlobals['unicast'] = 0
    sniffedGlobals['lastPrint'] = 0

    def recvOne(pkt):
        sg = sniffedGlobals
        if pkt.dst == 'ff:ff:ff:ff:ff:ff':
            sg['broadcast'] += 1
        else:
            sg['unicast'] += 1

        if time.time() > sg['lastPrint'] + PRINT_TIMEOUT:
            sg['lastPrint'] = time.time()
            printEntropy(sg['broadcast'], sg['unicast'])

    try:
        sc.sniff(iface=interface, prn=recvOne, store=0)
    except PermissionError:
        print("Error: Must be run as root to capture from interfaces", file=sys.stderr)
        return
    except OSError as e:
        if str(e).endswith('No such device'):
            print("Error: No such device '{interface}'", file=sys.stderr)
            return
        raise e

    print()

def getCounts(pkts):
    broadcast = len(pkts.filter(lambda p: p.dst == 'ff:ff:ff:ff:ff:ff'))
    return broadcast, len(pkts)-broadcast

def printEntropy(broadcast, unicast):
    print('\r',
          'broadcast=' + str(broadcast),
          'unicast=' + str(unicast),
          'entropy=' + str(getEntropy([unicast, broadcast])),
          ' '*10,
          end='')

def getEntropy(counts : List[int]):
    tot = sum(counts)
    return sum(map(lambda x: -x/tot * log2(x/tot) if x!=0 else 0, counts))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calculate interface entropy")

    parser_source = parser.add_mutually_exclusive_group()
    parser_source.add_argument('-i', '--interface',
            help="attach to given interface (default: use all)", type=str)
    parser_source.add_argument('-c', '--cap',
            help="read data from a pcap file", type=str)

    args = parser.parse_args()

    if args.cap is not None:
        readFromFile(args.cap)
    else:
        readFromIF(args.interface)

