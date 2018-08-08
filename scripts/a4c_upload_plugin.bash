#!/bin/bash

#
# a4c_upload_yorc_plugin.bash - uploads Yorc plugin in Alien4Cloud
#

a4cURL="http://localhost:8088"
yorcPluginURL="https://github.com/ystia/yorc-a4c-plugin/releases/download/v3.0.0/alien4cloud-yorc-plugin-3.0.0.zip"
usage() {
    echo ""
    echo "Usage:"
    echo "a4c_upload_yorc_plugin.bash [--a4c-url <Alien4Cloud URL>] [--yorc-plugin-url <Yorc URL>]"
    echo "   - default A4C URL        : $a4cURL"
    echo "   - default Yorc plugin URL: $yorcPluginURL"
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
    -y|--yorc-plugin-url)
    yorcPluginURL="$2"
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

# Check the plugin is not yet registered
curl --request GET \
         --url $a4cURL/rest/latest/plugins?query=alien4cloud-yorc-plugin \
         --header 'Accept: application/json' \
         --silent \
         --cookie cookies.a4c \
| grep --quiet alien4cloud-yorc-plugin

res=$?
if [ $res -eq 0 ]
    then
        echo "Plugin already registered"
        exit 0
fi

# Download Yorc plugin
echo "Downloading the plugin..."
curl --request GET \
         --url $yorcPluginURL \
         --location \
         --output yorcPlugin.zip

res=$?
if [ $res -ne 0 ]
then
    echo "Exiting on error downloading the plugin at $yorcPluginURL"
    exit 1
fi

curl --request POST \
         --url $a4cURL/rest/latest/plugins \
         --header 'Content-Type: multipart/form-data' \
         --cookie cookies.a4c \
         --silent \
         --form 'file=@yorcPlugin.zip' > /dev/null

res=$?
rm -f yorcPlugin.zip
if [ $res -ne 0 ]
then
    echo "Exiting on error uploading the plugin in Alien4Cloud"
    exit 1
else
    echo "Plugin registered in Alien4Cloud"
fi
