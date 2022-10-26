#!/bin/bash

# subscription_list=$(az account subscription list --query "[].displayName" --output tsv)
declare -a subscription_list=("AU-INNOVATION-SUB001" "AU-PREPROD-SUB001" "AU-PROD-SUB001" "AU-SHARED-SUB001"
"ilt-ppd-001" "mex-ppd-001" "pet-dev-002" "pet-tst-sub" "policy-ppd-001" "timeline" "sec-prd-001" "UK-PROD-SUB001"
"US-PROD-SUB001" "pet-dev-001")
k8s_locations=""

for sub in "${subscription_list[@]}"
do
  echo "Outputing AKS in ${sub} to files/sub_${sub}.json"
  echo $(az aks list --query '[].{Name:name, ResourceId:id, k8sversion:kubernetesVersion, Location:location, NodePools:agentPoolProfiles[].{Name:name, Version:currentOrchestratorVersion}}' --subscription ${sub}) \
  > files/sub_${sub}.json
  k8s_locations="${k8s_locations} $(az aks list --query '[].location' --subscription ${sub}| tr -d '\n,[]\"%')"
done

k8s_locations=$(echo ${k8s_locations} | tr " " "\n" | sort | uniq)

for location in $k8s_locations
do
  echo "Outputing AKS upgradable versions in region ${location} to files/loc_${location}.json"
  az aks get-versions --location $location > files/loc_${location}.json
done

echo "Generating AKS Version Report..."
python3 aks_report.py

rm files/*.json