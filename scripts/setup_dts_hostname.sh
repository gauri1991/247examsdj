#!/bin/bash

# Script to set up dts.com hostname for local development

echo "Setting up dts.com hostname for local development..."
echo ""
echo "This script will add an entry to /etc/hosts to map dts.com to your local IP."
echo "You'll need to run this with sudo."
echo ""

# Your local IP
LOCAL_IP="192.168.29.81"
HOSTNAME="dts.com"

# Check if entry already exists
if grep -q "$HOSTNAME" /etc/hosts; then
    echo "Entry for $HOSTNAME already exists in /etc/hosts"
    echo "Current entry:"
    grep "$HOSTNAME" /etc/hosts
else
    echo "Adding $LOCAL_IP $HOSTNAME to /etc/hosts..."
    echo "$LOCAL_IP    $HOSTNAME" | sudo tee -a /etc/hosts
    echo "Entry added successfully!"
fi

echo ""
echo "Setup complete! You can now access your Django app at:"
echo "http://dts.com:8000"
echo ""
echo "Note: Other devices on your network will also need to add this entry to their hosts file:"
echo "$LOCAL_IP    dts.com"