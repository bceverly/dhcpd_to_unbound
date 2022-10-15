#! /usr/local/bin/python3
"""
    dhcpd_to_unbound

    A tool that helps integrate dhcpd to unbound by parsing the leases
    file from dhcpd (normally in /var/db/dhcpd.leases) and converts it
    to a series of blank-line separated A records using a domain name
    specified on the command-line:

    dhcpd_to_unbound --input /var/db/dhcpd.leases --domain example.com
"""

import re
import argparse

class Lease:
""" 
    A class to manage the contents of a dhcpd lease record 
"""
    hostname = None
    mac_address = None
    abandoned = None

    def __init__(self,hostname,mac_address,abandoned):
        self.hostname = hostname
        self.mac_address = mac_address
        self.abandoned = abandoned


def ParseFile(filename):
"""
    A function to parse the dhcpd.leases file

    Arguments:
    filename - the filename of the dhcpd.leases file (full path)

    Returns:
    A dictionary of Lease objects with the string of the ipv4 address
    as the key
"""
    file = open(filename, 'r')
    Lines = file.readlines()

    dict = {}
    current_ip = None
    current_lease = Lease(None,None,None)

    for line in Lines:
        words = line.split(" ")
        if line.startswith("lease"):
            if current_ip == None:
                # First time through
                current_ip = words[1]
            else:
                if (dict.get(current_ip) == None):
                    dict[current_ip] = current_lease
                    current_lease = Lease(None,None,False)
                current_ip = words[1]
        elif len(words) > 0 and words[0].strip() == 'client-hostname':
            hostname = words[1].strip()
            hostname = re.sub('"','',hostname)
            hostname = re.sub(';','',hostname)
            current_lease.hostname = hostname
        elif len(words) > 0 and words[0].strip() == 'hardware':
            mac_address = words[2].strip()
            mac_address = re.sub(';','',mac_address)
            current_lease.mac_address = mac_address
        elif len(words) > 0 and words[0].strip() == "abandoned;":
            current_lease.abandoned = True

    # Add the last one
    if dict.get(current_ip == None):
        dict[current_ip] = current_lease

    return dict


def WriteOutput(dict, domain_name):
"""
    Write out a list of blank line separated A records in a format used
    by unbound from the list of lease objects

    Arguments:
    dict - the dictionary of Lease objects produced by the Parse function
        above
    domain-name - the domain name (ex. example.org) that is to be appended
        to the hostnames supplied by the Parse function in the dictionary
"""
    print("# DNS A records for active DHCP (dhcpd) leases")
    print("#")
    print("# File created using dhcpd_to_unbound (https://github.com/bceverly/dhcpd_to_unbound)")
    print("")
    for key in dict.keys():
        if not dict[key].abandoned and not dict[key].hostname == None:
            print('local-data: "{0}.{2}. IN A {1}"'.format(dict[key].hostname, key, domain_name))
            print('local-data-ptr: "{0} {1}.{2}"'.format(key, dict[key].hostname, domain_name))
            print('')


if __name__ == "__main__":
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='Produce live unbound A records from the dhcpd leases data.')
    parser.add_argument('-i','--input', metavar='filepath', type=str,
            help='The dhcpd.leases file to be parsed', required=True,
            dest='input_file')
    parser.add_argument('-d','--domain', metavar='example.com', type=str,
            required=True, help='The domain name to append to the hostnames',
            dest='domain_name')
    args = parser.parse_args()

    # Perform the translation
    dict = ParseFile(args.input_file)
    WriteOutput(dict, args.domain_name)
