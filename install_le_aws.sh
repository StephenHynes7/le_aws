#!/bin/bash

################################################
#                                              #
#  This script installs various                #
#  components that are necessary to            #
#  run the logentries aws setup script.        #
#                                              # 
################################################

# Fail on error
set -e

#################################################
# Get info about system: 
# https://github.com/coto/server-easy-install/blob/master/lib/core.sh
#################################################

lowercase(){
    echo "$1" | sed "y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/"
}

shootProfile(){
    OS=`lowercase \`uname\``
    KERNEL=`uname -r`
    MACH=`uname -m`

    if [ "${OS}" == "windowsnt" ]; then
	OS=windows
    elif [ "${OS}" == "darwin" ]; then
	OS=mac
    else
	OS=`uname`
	if [ "${OS}" = "SunOS" ] ; then
	    OS=Solaris
	    ARCH=`uname -p`
	    OSSTR="${OS} ${REV}(${ARCH} `uname -v`)"
	elif [ "${OS}" = "AIX" ] ; then
	    OSSTR="${OS} `oslevel` (`oslevel -r`)"
	elif [ "${OS}" = "Linux" ] ; then
	    if [ -f /etc/redhat-release ] ; then
		DistroBasedOn='RedHat'
		DIST=`cat /etc/redhat-release |sed s/\ release.*//`
		PSUEDONAME=`cat /etc/redhat-release | sed s/.*\(// | sed s/\)//`
		REV=`cat /etc/redhat-release | sed s/.*release\ // | sed s/\ .*//`
	    elif [ -f /etc/SuSE-release ] ; then
		DistroBasedOn='SuSe'
		PSUEDONAME=`cat /etc/SuSE-release | tr "\n" ' '| sed s/VERSION.*//`
		REV=`cat /etc/SuSE-release | tr "\n" ' ' | sed s/.*=\ //`
	    elif [ -f /etc/mandrake-release ] ; then
		DistroBasedOn='Mandrake'
		PSUEDONAME=`cat /etc/mandrake-release | sed s/.*\(// | sed s/\)//`
		REV=`cat /etc/mandrake-release | sed s/.*release\ // | sed s/\ .*//`
	    elif [ -f /etc/debian_version ] ; then
		DistroBasedOn='Debian'
		DIST=`cat /etc/lsb-release | grep '^DISTRIB_ID' | awk -F= '{ print $2 }'`
		PSUEDONAME=`cat /etc/lsb-release | grep '^DISTRIB_CODENAME' | awk -F= '{ print $2 }'`
		REV=`cat /etc/lsb-release | grep '^DISTRIB_RELEASE' | awk -F= '{ print $2 }'`
	    fi
	    if [ -f /etc/UnitedLinux-release ] ; then
		DIST="${DIST}[`cat /etc/UnitedLinux-release | tr "\n" ' ' | sed s/VERSION.*//`]"
	    fi
	    OS=`lowercase $OS`
	    DistroBasedOn=`lowercase $DistroBasedOn`
	    readonly OS
	    readonly DIST
	    readonly DistroBasedOn
	    readonly PSUEDONAME
	    readonly REV
	    readonly KERNEL
	    readonly MACH
	fi	
    fi
}
shootProfile
echo "OS: $OS"
echo "DIST: $DIST"
echo "PSUEDONAME: $PSUEDONAME"
echo "REV: $REV"
echo "DistroBasedOn: $DistroBasedOn"
echo "KERNEL: $KERNEL"
echo "MACH: $MACH"
echo "========"


#################################################
# Get info about system: 
# https://github.com/coto/server-easy-install/blob/master/lib/core.sh
#################################################

if command -v python >/dev/null; then
    if python -c 'import sys; (sys.exit(1) if sys.version_info >= (2,6) else sys.exit(0));' >/dev/null ]; then
	echo "Version of python is supported"
    else:
	echo "Python version >= 2.6 is required."
	exit 1; 
    fi;
else
    echo "Python could not be found and is required."
    exit 1;
fi;
# install pip and python-dev if not present on the system
# Debian/Ubuntu
#if [ "$DistroBasedOn" == "debian" ]; then
if command -v apt-get >/dev/null; then
    # Installing wget
    echo "Installing wget if not already present."
    sudo apt-get install wget
    # TODO: should we avoid installing python-dev and paramiko for a 'local' setup?
    echo "Installing python-dev"
    sudo apt-get install python-dev
elif command -v yum >/dev/null; then
    # Installing wget
    echo "Installing wget if not already present."
    sudo yum install wget
    # TODO: should we avoid installing python-dev and paramiko for a 'local' setup?
    echo "Installing python-dev"
    sudo yum install python-devel
elif [ "$OS" == "mac" ]; then
    # Checking the presence of python development tools and headers: http://stackoverflow.com/questions/4848566/check-for-existence-of-python-dev-files-from-bash-script 
    # get include path for this python version
    INCLUDE_PY=$(python -c "from distutils import sysconfig as s; print s.get_config_vars()['INCLUDEPY']")
    if [ ! -f "${INCLUDE_PY}/Python.h" ]; then
       echo "Python development headers and tools could not be found. Please install them first (e.g. thourgh Xcode)." >&2
       exit 3;
    fi
elif [ "$OS" == "linux" ]; then
    echo "Neither apt-get nor yum were found on this system. One or the other is required to complete the installation.";
    exit 1;
else
    echo "System $OS is not currently supported."
    exit 1;
fi

# create working directory
if [ ! -d le_aws ]; then
    mkdir le_aws;
fi
cd le_aws
WORKING_DIR=`pwd`

# install virutalenv
if command -v wget >/dev/null; then
   wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.tar.gz
elif command -v curl >/dev/null ; then
   curl -O --insecure https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.tar.gz
fi
tar xvfz virtualenv-1.10.tar.gz
python virtualenv-1.10/virtualenv.py env

#GIT_REPO_LOCATION=file:///home/benoit/Logentries/git_repo/awswork

# install boto and paramiko in the virtual environment
env/bin/pip install boto
env/bin/pip install fabric
env/bin/pip install logentries

# Install LogentriesSDK and LogentriesProvisioning
#git clone git@github.com:bgaudin/le_aws.git
#cd le_aws/LogentriesProvisioning
#git checkout devel
#$WORKING_DIR/env/bin/python setup.py sdist
#cd ../LogentriesSDK
#$WORKING_DIR/env/bin/python setup.py sdist
#cd ../../
#env/bin/pip install file://$WORKING_DIR/le_aws/LogentriesSDK/dist/LogentriesSDK-0.1.0.tar.gz
#env/bin/pip install file://$WORKING_DIR/le_aws/LogentriesProvisioning/dist/LogentriesProvisioning-0.1.0.tar.gz
# TODO: check if unzipping this is an issue on Mac OS X
BRANCH=devel
env/bin/pip install https://raw.github.com/bgaudin/le_aws/$BRANCH/LogentriesSDK/dist/LogentriesSDK-0.1.0.tar.gz
env/bin/pip install https://raw.github.com/bgaudin/le_aws/$BRANCH/LogentriesProvisioning/dist/LogentriesProvisioning-0.1.0.tar.gz

# Create aws conf file
echo '{"aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",' >> aws.json
echo '"aws_access_key_id": "AWS_ACCESS_KEY_ID",' >> aws.json
echo '"usernames": ["ec2-user","root","ubuntu"],' >> aws.json
echo '"filters": [' >> aws.json
echo '{"ec2_filter": {},' >> aws.json
echo '"log_filter": "^/var/log/.*\\.log"}' >> aws.json
echo '],' >> aws.json
echo '"ssh_key_paths": ["~/.ssh/"]}' >> aws.json

# Create logentries conf file
echo '{"account_key": "ACCOUNT_KEY_HERE"}' >> logentries.json

WORKING_DIR=`pwd`
# Create sync setup command
echo "#! $WORKING_DIR/env/bin/python" >> sync
echo 'import os' >> sync
echo 'import sys' >> sync
echo 'from logentriesprovisioning import sync_log' >> sync
echo "sync_log.main(os.getcwd(),(sys.argv[1] if len(sys.argv)>0 else '')" >> sync
echo 'print (sys.argv[1] if len(sys.argv)>0 else '')' >> sync
chmod +x sync

# Create aws setup command
echo "#! $WORKING_DIR/env/bin/python" >> aws_setup
echo 'import os' >> aws_setup
echo 'from logentriesprovisioning import aws_client' >> aws_setup
echo 'from logentriesprovisioning import sync_log' >> aws_setup
echo 'aws_client.create_ssh_config(working_dir=os.getcwd())' >> aws_setup
echo 'sync_log.main(working_dir=os.getcwd())' >> aws_setup
chmod +x aws_setup
