#!/bin/bash

#
# a4c_create_orchestrator.bash - creates a Yorc orchestrator in Alien4Cloud
# Prerequisite: the Yorc Alien4Cloud plugin was registered in Alien4Cloud
#               (see a4c_upload_plugin.bash)
#

a4cURL="http://localhost:8088"
yorcURL="http://localhost:8800"
usage() {
    echo ""
    echo "Usage:"
    echo "a4c_create_orchestrator.bash [--a4c-url <Alien4Cloud URL>] [--yorc-url <Yorc URL>]"
    echo "   - default A4C URL        : $a4cURL"
    echo "   - default Yorc plugin URL: $yorcPluginURL"
    exit 1
}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -a|--a4c-url)
    a4cURL="$2"
    shift # past argument
    shift # past value
    ;;
    -y|--yorc-url)
    yorcURL="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help)
    usage
    exit 0
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# First, login and store the cookie
curl -d "username=admin&password=admin&submit=Login"  \
     --url  $a4cURL/login \
     --dump-header headers \
	 --silent \
     --cookie-jar cookies.a4c

# Check if a Yorc orchestrator alreays exists
curl --request GET \
         --url $a4cURL/rest/latest/orchestrators?query=Yorc \
         --header 'Accept: application/json' \
         --silent \
         --cookie cookies.a4c \
| grep --quiet Yorc

res=$?
if [ $res -eq 0 ]
    then
        echo "Orchestrator already registered"
        exit 0
fi

# Create the orchestrator
curl --request POST \
         --url $a4cURL/rest/latest/orchestrators \
         --header 'Content-Type: application/json' \
         --cookie cookies.a4c \
         --silent \
          --data "{\"name\": \"Yorc\", \"pluginId\": \"alien4cloud-yorc-plugin\", \"pluginBean\": \"yorc-orchestrator-factory\"}" > /dev/null

res=$?
if [ $res -ne 0 ]
then
    echo "Exiting on error creating the orchestrator in Alien4Cloud"
    exit 1
fi
