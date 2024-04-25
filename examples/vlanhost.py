#!/usr/bin/env python3
"""
vlanhost.py: Host subclass that uses a VLAN tag for the default interface.

Dependencies:
    This class depends on the "vlan" package
    $ sudo apt-get install vlan

Usage (example uses VLAN ID=1000):
    From the command line:
        sudo mn --custom vlanhost.py --host vlan,vlan=1000

    From a script (see exampleUsage function below):
        from functools import partial
        from vlanhost import VLANHost

        ....

        host = partial( VLANHost, vlan=1000 )
        net = Mininet( host=host, ... )

    Directly running this script:
        sudo python vlanhost.py 1000

"""

import sys
from mininet.node import Host
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.log import error

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel

from functools import partial

class VLANHost( Host ):
    "Host connected to VLAN interface"

    # Alternatively, one could define
    # def config(self, vlan=None, **params)
    # and avoid the
    # vlan = params.pop('vlan' None)
    # pylint: disable=arguments-differ
    def config( self, **params ):
        """Configure VLANHost according to (optional) parameters:
           vlan: VLAN ID for default interface"""

        vlan = params.pop('vlan', None)
        assert vlan is not None, 'VLANHost without vlan in instantiation'
        r = super().config(**params)

        intf = self.defaultIntf()
        ip_info = params['ip']
        new_intf = f'{intf}.{vlan}'
        # remove IP from default, "physical" interface
        self.cmd( f'ip address del {ip_info} dev {intf}')
        # create VLAN interface
        self.cmd(f'ip link add link {intf} name {new_intf} type vlan id {vlan}')
        # assign the host's IP to the VLAN interface
        self.cmd( f'ip address add {ip_info} dev {new_intf}')
        self.cmd( f'ip link set up dev {new_intf}')
        # update the (Mininet) interface to refer to VLAN interface name
        intf.name = new_intf
        # add VLAN interface to host's name to intf map
        self.nameToIntf[ new_intf ] = intf

        return r


hosts = { 'vlan': VLANHost }


def exampleAllHosts( vlan ):
    """Simple example of how VLANHost can be used in a script"""
    # This is where the magic happens...
    host = partial( VLANHost, vlan=vlan )
    # vlan (type: int): VLAN ID to be used by all hosts

    # Start a basic network using our VLANHost
    topo = SingleSwitchTopo( k=2 )
    net = Mininet( host=host, topo=topo, waitConnected=True )
    net.start()
    CLI( net )
    net.stop()

# pylint: disable=arguments-differ

class VLANStarTopo( Topo ):
    """Example topology that uses host in multiple VLANs

       The topology has a single switch. There are k VLANs with
       n hosts in each, all connected to the single switch. There
       are also n hosts that are not in any VLAN, also connected to
       the switch."""

    def build( self, k=2, n=2, vlanBase=100 ):
        s1 = self.addSwitch( 's1' )
        for i in range( k ):
            vlan = vlanBase + i
            for j in range(n):
                name = f'h{j+1}-{vlan}'
                h = self.addHost(name, cls=VLANHost, vlan=vlan)
                self.addLink(h, s1)
        for j in range(n):
            h = self.addHost(f'h{j+1}')
            self.addLink(h, s1 )


def exampleCustomTags():
    """Simple example that exercises VLANStarTopo"""

    net = Mininet( topo=VLANStarTopo(), waitConnected=True )
    net.start()
    CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )

    # Using the 'ip' command everywhere, there is no need for extra packages
    if len( sys.argv ) >= 2:
        exampleAllHosts( vlan=int( sys.argv[ 1 ] ) )
    else:
        exampleCustomTags()
