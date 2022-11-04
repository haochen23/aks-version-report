#!/bin/bash

# $1 to be a list of comma separated resource groups
# $2 to be the subscription id

subscription=$(az account subscription show --id $2 --query "displayName" | tr -d '"')

for i in ${1//,/ }
do
    # call your procedure/other scripts here below
    echo $(az resource list --resource-group $i --subscription $2 --query '[].{Name:name, Type:type, Location:location, Repo:tags.Repo, Id:id}' --subscription $2) \
  > files/${subscription}__${i}.json
done



