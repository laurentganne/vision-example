#!/bin/bash

#
# utils - Library of functions used to perform Alien4Cloud REST calls
#

#
# a4c_login - login on Alien4Cloud anf store cookies
# Expects 4 parameters :
# - URL of Alien4Cloud
# - user name
# - password
# - file where to store cookies
a4c_login() {
   if [ $# != 4 ]
   then
       echo "Usage:"
       echo "a4c_login.bash <URL> <user> <password> <file where to store cookies>"
       exit 1
   fi

    curl -d "username=$2&password=$3&submit=Login"  \
         --url  $1/login \
         --dump-header headers \
	     --silent \
         --cookie-jar $4

}
