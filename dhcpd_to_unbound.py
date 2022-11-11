#!/usr/bin/env python3
"""
dhcpd_to_unbound

A tool that helps integrate dhcpd to unbound by parsing the leases
file from dhcpd (normally in /var/db/dhcpd.leases) and converts it
to a series of blank-line separated A records using a domain name
specified on the command-line:

dhcpd_to_unbound --input /var/db/dhcpd.leases --domain example.com
"""

import argparse


class Lease:
    """ 
    A class to manage the contents of a dhcpd lease record 
    """
    hostname = None
    mac_address = None
    abandoned = None

    def __init__(self, hostname=None, mac_address=None, abandoned=None):
        self.hostname = hostname
        self.mac_address = mac_address
        self.abandoned = abandoned


def parse_file(filename):
    """
    A function to parse the dhcpd.leases file

    Arguments:
    filename - the filename of the dhcpd.leases file (full path)

    Returns:
    A dictionary of Lease objects with the string of the ipv4 address
    as the key
    """
    leases = {}
    current_ip = None
    current_lease = Lease()

    with open(filename) as fp:
        for line in fp:
            words = line.strip().split(' ')

            if line.startswith('lease'):
                if current_ip is not None and current_ip not in leases:
                    # Not the first time through.
                    leases[current_ip] = current_lease
                    current_lease = Lease(abandoned=False)

                current_ip = words[1]
            elif len(words) > 0 and words[0].strip() == 'client-hostname':
                hostname = words[1].strip()
                hostname = hostname.replace('"', '').replace(';', '')
                current_lease.hostname = hostname
            elif len(words) > 0 and words[0].strip() == 'hardware':
                mac_address = words[2].strip()
                mac_address = mac_address.replace(';', '')
                current_lease.mac_address = mac_address
            elif len(words) > 0 and words[0].strip() == 'abandoned;':
                current_lease.abandoned = True

    # Add the last one
    if current_ip not in leases:
        leases[current_ip] = current_lease

    return leases


def write_output(leases, domain_name):
    """
    Write out a list of blank line-separated A records in a format used
    by unbound from the list of lease objects.

    Arguments:
    leases - the dictionary of Lease objects produced by the parse_file
        above
    domain_name - the domain name (ex. example.org) that is to be appended
        to the hostnames supplied by the parse_file in the dictionary
    """
    print('# DNS A records for active DHCP (dhcpd) leases\n'
          '#\n'
          '# File created using dhcp_to_unbound '
          '(https://github.com/bceverly/dhcp_to_unbound)\n')

    for key, value in leases.items():
        if not (value.abandoned or value.hostname is None):
            print(f'local-data: "{value.hostname}.{domain_name}. IN A {key}"\n'
                  f'local-data-ptr: "{key} {value.hostname}.{domain_name}"\n')


if __name__ == '__main__':
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='Produce live unbound A '
                                     'records from the dhcpd leases data.')
    parser.add_argument(
        '-i', '--input', metavar='filepath', type=str,
        help='The dhcpd.leases file to be parsed', required=True,
        dest='input_file')
    parser.add_argument(
        '-d', '--domain', metavar='example.com', type=str,
        required=True, help='The domain name to append to the hostnames',
        dest='domain_name')

    args = parser.parse_args()

    # Perform the translation
    leases = parse_file(args.input_file)
    write_output(leases, args.domain_name)
