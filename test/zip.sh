#!/bin/sh
#
# exit 0 for success other for failed
#
#

if [ $# -ne 2 ] ; then
    echo "Error params"
    exit 1
fi

CONFIG_VERSION=$1
GAME_VERSION=$2

echo "got config_version=${CONFIG_VERSION} game_version=${GAME_VERSION}"

exit 0
