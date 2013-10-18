#!/bin/sh

set -e # Exit script immediately on first error.
set -x # Print commands and their arguments as they are executed.

ssh-add ~/.ssh/id_rsa_logentries

CURRENT_DIR=`pwd`
WORKING_DIR=/tmp
cd $WORKING_DIR
vagrant destroy --force
if [ -f VagrantFile ]; then
    echo "Removing existing VagrantFile."
    rm VagrantFile
fi
cd $CURRENT_DIR
cp vagrant_template $WORKING_DIR/VagrantFile

cd $WORKING_DIR
vagrant up

ssh -F $CURRENT_DIR/ssh_config precise32
