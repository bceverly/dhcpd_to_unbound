# dhcpd_to_unbound
A tool that helps integrate dhcpd to unbound

The application parses the contents of a dhcpd.leases file that contains the current status of DHCP leases on a system.  This file typically will exist in /var/db/dhcpd.leases on an OpenBSD system.  The output of the application is sent to stdout and is a blank line separated list of DNS A records that correspond to the IP to hostname mappings in the leases file.  A domain name parameter is required in order to be appended to the hostname from the leases file so that a FQDN is put in the A record.

Usage:

dhcpd_to_unbound --input /var/db/dhcpd.leases --domain example.com > /var/unbound/etc/dynamic.conf

This will produce output that can be redirected to a file that is input into the unbound.conf file through the se of the include syntax:

/var/unbound/etc/unbound.conf:
...
include: "dynamic.conf"
...
