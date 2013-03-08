#!/usr/bin/env python
# This script will get all puppet modules required
# for the deployment of the Cisco OpenStack Edition (COE).
# Set REPO_NAME below to the name of the yum or apt repository you want to use.
# Choices include:
#    * A main release repo.  This will include the latest tested and 
#      released modules.  This is the recommended choice for most users.
#      Example: "folsom"
#    * A proposed repo.  This includes the latest code that developers have
#      committed.  It is considered bleeding edge and may not have been
#      fully vetted.  This is recommended only for developers.
#      Example: "folsom-proposed"
#    * A specific maintenance release repo.  This allows you to download
#      modules from a specific release.  This is recomended option if you
#      have qualified only a specific release for your environment and do
#      not wish to (yet) use the latest stable updates.
#      Example: "folsom/snapshots/2012.2.2"

import os
import sys
import optparse
import platform
import tempfile
from subprocess import STDOUT, check_call


#-------- Default Constants ---------------------

##TODO: Some of these could be made configurable via cmdline.
MODULE_FILE = "modules.list"
REPO_NAME = "folsom"
PUPPET_PATH = "/etc/puppet/"

# config file locations for yum and apt
APT_CONFIG_FILE = "/etc/apt/sources.list.d/cisco-openstack-mirror_folsom.list"
YUM_CONFIG_FILE = "/etc/yum.repos.d/cisco-openstack-mirror.repo"

# gpg keys for yum and apt repos with which packages are signed
APT_REPO_KEY = """-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.11 (GNU/Linux)

mQENBE/oXVkBCACcjAcV7lRGskECEHovgZ6a2robpBroQBW+tJds7B+qn/DslOAN
1hm0UuGQsi8pNzHDE29FMO3yOhmkenDd1V/T6tHNXqhHvf55nL6anlzwMmq3syIS
uqVjeMMXbZ4d+Rh0K/rI4TyRbUiI2DDLP+6wYeh1pTPwrleHm5FXBMDbU/OZ5vKZ
67j99GaARYxHp8W/be8KRSoV9wU1WXr4+GA6K7ENe2A8PT+jH79Sr4kF4uKC3VxD
BF5Z0yaLqr+1V2pHU3AfmybOCmoPYviOqpwj3FQ2PhtObLs+hq7zCviDTX2IxHBb
Q3mGsD8wS9uyZcHN77maAzZlL5G794DEr1NLABEBAAG0NU9wZW5TdGFja0BDaXNj
byBBUFQgcmVwbyA8b3BlbnN0YWNrLWJ1aWxkZEBjaXNjby5jb20+iQE4BBMBAgAi
BQJP6F1ZAhsDBgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRDozGcFPtOxmXcK
B/9WvQrBwxmIMV2M+VMBhQqtipvJeDX2Uv34Ytpsg2jldl0TS8XheGlUNZ5djxDy
u3X0hKwRLeOppV09GVO3wGizNCV1EJjqQbCMkq6VSJjD1B/6Tg+3M/XmNaKHK3Op
zSi+35OQ6xXc38DUOrigaCZUU40nGQeYUMRYzI+d3pPlNd0+nLndrE4rNNFB91dM
BTeoyQMWd6tpTwz5MAi+I11tCIQAPCSG1qR52R3bog/0PlJzilxjkdShl1Cj0RmX
7bHIMD66uC1FKCpbRaiPR8XmTPLv29ZTk1ABBzoynZyFDfliRwQi6TS20TuEj+ZH
xq/T6MM6+rpdBVz62ek6/KBcuQENBE/oXVkBCACgzyyGvvHLx7g/Rpys1WdevYMH
THBS24RMaDHqg7H7xe0fFzmiblWjV8V4Yy+heLLV5nTYBQLS43MFvFbnFvB3ygDI
IdVjLVDXcPfcp+Np2PE8cJuDEE4seGU26UoJ2pPK/IHbnmGWYwXJBbik9YepD61c
NJ5XMzMYI5z9/YNupeJoy8/8uxdxI/B66PL9QN8wKBk5js2OX8TtEjmEZSrZrIuM
rVVXRU/1m732lhIyVVws4StRkpG+D15Dp98yDGjbCRREzZPeKHpvO/Uhn23hVyHe
PIc+bu1mXMQ+N/3UjXtfUg27hmmgBDAjxUeSb1moFpeqLys2AAY+yXiHDv57ABEB
AAGJAR8EGAECAAkFAk/oXVkCGwwACgkQ6MxnBT7TsZng+AgAnFogD90f3ByTVlNp
Sb+HHd/cPqZ83RB9XUxRRnkIQmOozUjw8nq8I8eTT4t0Sa8G9q1fl14tXIJ9szzz
BUIYyda/RYZszL9rHhucSfFIkpnp7ddfE9NDlnZUvavnnyRsWpIZa6hJq8hQEp92
IQBF6R7wOws0A0oUmME25Rzam9qVbywOh9ZQvzYPpFaEmmjpCRDxJLB1DYu8lnC4
h1jP1GXFUIQDbcznrR2MQDy5fNt678HcIqMwVp2CJz/2jrZlbSKfMckdpbiWNns/
xKyLYs5m34d4a0it6wsMem3YCefSYBjyLGSd/kCI/CgOdGN1ZY1HSdLmmjiDkQPQ
UcXHbA==
=v6jg
-----END PGP PUBLIC KEY BLOCK-----"""
##TODO: Once we have a gpg for redhat manifest packages, include it here.
YUM_REPO_KEY = """TBD"""

##TODO: replace this with right url location once in place. Ideally
# we want a generic url with type and dist info. For example:
# http://eng.cisco.com/openstack/cisco/$type/dist/$release/
# where $type = 'yum' or 'apt'; $release= 'folsum' or 'grizzly' etc.

# yum repo url and .repo file setup
YUM_REPO_URL = "ftp://ftpeng.cisco.com/openstack/cisco/fedora/dist/grizzly"
YUM_REPO_DATA = """
[cisco-openstack-mirror]
name=Cisco Openstack Repository
baseurl= %(repo_url)s
enabled=1
gpgcheck=1
gpgkey=%(repo_url)s/coe.pub
""" % {'repo_url' : YUM_REPO_URL}

# APT repo url and source file setup
APT_REPO_URL = "ftp://ftpeng.cisco.com/openstack/cisco"
APT_REPO_DATA="""
# cisco-openstack-mirror_folsom
deb %(repo_url)s %(repo_name)s main
deb-src %(repo_url)s %(repo_name)s main""" % {'repo_url' : APT_REPO_URL, 
                                              'repo_name' :REPO_NAME}

# --- helper calls to fetch the modules ----------


def get_modules(modules_file=MODULE_FILE):
    """
     Read the module list file and get a list of all module names.
     We need to prepend the module name with "puppet-" to match the
     package names.
    """
    return ["puppet-"+ line.strip() for line in open(modules_file)]


def get_distribution():
    """
     Get the distribution we're dealing with
    """
    return platform.dist()[0]


def setup_apt_repo():
    """
     Setup apt repo to install manifest packages via apt
    """
    if os.path.exists(APT_CONFIG_FILE):
        print("Repo already in %s; assuming it is correct and not adding an additional repo configuration." % APT_CONFIG_FILE)
        return 
    # no config file found, lets set one up
    with open(APT_CONFIG_FILE, 'a') as f:
        f.write(APT_REPO_DATA)
    # add gpg key to apt
    apt_key_add()


def apt_key_add():
    """
     Add the gpg key to apt repository
    """
    with tempfile.NamedTemporaryFile() as temp:
       temp.write(APT_REPO_KEY)
       temp.flush()
       check_call(['apt-key', 'add', temp.name],
             stdout=open(os.devnull,'wb'), stderr=STDOUT) 

def apt_update():
    """
     Update apt repo
    """
    check_call(['apt-get', 'update'],
         stdout=open(os.devnull,'wb'), stderr=STDOUT)

def apt_install(modules):
    """
     Install packages via apt
    """
    apt_update()
    check_call(['apt-get', 'install', '-y', " ".join(modules)],
         stdout=open(os.devnull,'wb'), stderr=STDOUT) 


def setup_yum_repo():
    """
     Setup yum repos to install package manifests via yum.
     We just download the .repo file from the yum repo url.
     Example yum repo file is as follows:
     [cisco-openstack-mirror]
     name=Cisco Openstack Repository
     baseurl=ftp://ftpeng.cisco.com/openstack/cisco/yum/dist/grizzly/
     enabled=1
     gpgcheck=1
     gpgkey=ftp://ftpeng.cisco.com/openstack/cisco/yum/dist/grizzly/coe.pub
     
    """
    if os.path.exists(YUM_CONFIG_FILE):
        print("Repo already in %s; assuming it is correct and not adding an additional repo configuration." % YUM_CONFIG_FILE)
        return
    # no config found, let download from the repo url 
    with open(YUM_CONFIG_FILE, 'wb') as repo_file:
        repo_file.write(YUM_REPO_DATA)
 


def yum_install(modules):
    """
     Install packages via yum
    """
    check_call(['yum', 'install', '-y', " ".join(modules)],
         stdout=open(os.devnull,'wb'), stderr=STDOUT) 


def main():
    """
     This main call does the following:
      - Parse the modules file and get list of packages
      - Check the distribution we're working with yum/apt
      - Perform repo setup for yum or apt repos
      - install necessary packages
    """
    # parse and get list of modules
    modules = get_modules(MODULE_FILE)
    
    # set up the repos and perform install
    distro = get_distribution().lower() 
    if distro in ["redhat", "fedora"]:
       setup_yum_repo()
       yum_install(modules)
    elif distro in ["ubuntu",]:
       setup_apt_repo()
       apt_install(modules)


if __name__=='__main__':
    main()
