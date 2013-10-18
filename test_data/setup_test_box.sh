#!/bin/sh

set -e # Exit script immediately on first error.
set -x # Print commands and their arguments as they are executed.

# Create two new users and set ssh keys
USERNAME=test_user
SSH_DIR_USER=/home/$USERNAME/.ssh

SUDO_USERNAME=sudo_user
SSH_DIR_SUDO_USER=/home/$SUDO_USERNAME/.ssh

if id -u $USERNAME >/dev/null 2>&1; then
        echo "user already exists"
else
	adduser --disabled-password $USERNAME
fi

if id -u $SUDO_USERNAME >/dev/null 2>&1; then
        echo "user already exists"
else
	adduser --disabled-password $SUDO_USERNAME
fi
# Add sudo_user to the admin group so that they have sudo privileges
usermod -g admin $SUDO_USERNAME

# Set ssh key for user 
if [ ! -d $SSH_DIR_USER ]; then
    mkdir $SSH_DIR_USER
fi
if [ ! -f $SSH_DIR_USER/authorized_keys ]; then
    touch $SSH_DIR_USER/authorized_keys
fi
cat /vagrant/test_key.pub >> $SSH_DIR_USER/authorized_keys
chown -R $USERNAME:$USERNAME $SSH_DIR_USER

# Set ssh key for sudo user 
if [ ! -d $SSH_DIR_SUDO_USER ]; then
    mkdir $SSH_DIR_SUDO_USER
fi
if [ ! -f $SSH_DIR_SUDO_USER/authorized_keys ]; then
    touch $SSH_DIR_SUDO_USER/authorized_keys
fi
cat /vagrant/test_sudo_key.pub >> $SSH_DIR_SUDO_USER/authorized_keys
chown -R $SUDO_USERNAME:$SUDO_USERNAME $SSH_DIR_SUDO_USER
