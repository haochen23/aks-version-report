from abc import ABC, abstractmethod
from importlib import resources
import os
import json
import glob
import pandas as pd
from collections import OrderedDict
from dataclasses import dataclass
from az.cli import az


class FileCombiner(ABC):

    @abstractmethod
    def combine_files_to_dict(self):
        pass


class JsonCombiner(FileCombiner):

    def __init__(self, folder_path: str, glob_pattern: str = "*.json") -> None:
        super().__init__()
        self.resources = list()
        self.folder_path = folder_path
        self.glob_pattern = glob_pattern
        self.combine_files_to_dict()

    def combine_files_to_dict(self):

        for filename in glob.glob(os.path.join(self.folder_path, self.glob_pattern)):

            with open(filename) as f:
                # no time spend on slicing, hardcoded for now
                subscription_n_rg = filename.split(
                    '/')[-1].split('.')[0].split('__')
                data = json.load(f)
                for item in data:
                    item["ResourceGroup"] = subscription_n_rg[1]
                    item["Subscription"] = subscription_n_rg[0]
                self.resources.extend(data)


@dataclass(frozen=True)
class Resource:
    Location: str
    Name: str
    Repo: str
    Type: str
    ResourceGroup: str
    Subscription: str


class ResourceSummarizer:

    def __init__(self, combined_dict: JsonCombiner) -> None:
        self.all_resource_list = [
            Resource(**resource) for resource in combined_dict.resources]
        self.vms = []
        self.windows_vms = []
        self.linux_vms = []
        self.sql_vms = []
        self.sql_mi = []
        self.aks = []
        self.azure_sql = []
        self.backup_query_exit, self.backup_status = self._get_backup_status()

    def categorize_resources(self):
        for resource in self.all_resource_list:
            if resource.Type == "Microsoft.Compute/virtualMachines":
                self.vms.append(resource)
            elif resource.Type == "Microsoft.SqlVirtualMachine/SqlVirtualMachines":
                self.sql_vms.append(resource)
            elif resource.Type == "Microsoft.Sql/managedInstances":
                self.sql_mi.append(resource)
            elif resource.Type == "Microsoft.Sql/servers":
                self.azure_sql.append(resource)
            elif resource.Type == "Microsoft.ContainerService/managedClusters":
                self.aks.append(resource)

    def _get_backup_status(self):

        query = """
                Resources | where type in~ ("microsoft.compute/virtualmachines","microsoft.classiccompute/virtualmachines") | extend armResourceId = id
                | extend resourceId=tolower(armResourceId) | join kind = leftouter ( RecoveryServicesResources
//| where type == "microsoft.recoveryservices/vaults/backupfabrics/protectioncontainers/protecteditems"
//| where properties.backupManagementType == "AzureIaasVM"
//| where properties.workloadType in~ ("VM")
| extend lastBackup_status = properties.lastBackupStatus
| extend protection_status = properties.protectionStatus
| extend policy_name = properties.policyInfo.name
| extend lastbackup = properties.lastBackupTime
| extend lastRecoveryPoint = properties.lastRecoveryPoint
| project resourceId = tolower(tostring(properties.sourceResourceId)), backupItemid = id, policy_name, lastBackup_status, protection_status, lastbackup, lastRecoveryPoint, isBackedUp = isnotempty(id) ) on resourceId
//| extend isProtected = isnotempty(backupItemid) | where (isProtected == (0))
| extend sku_2 = properties.storageProfile.imageReference.sku
| extend publisher = properties.storageProfile.imageReference.publisher
| extend offer = properties.storageProfile.imageReference.offer
| extend osType = properties.storageProfile.osDisk.osType
| extend osVersion = properties.extended.instanceView.osVersion
| extend osName = properties.extended.instanceView.osName
| extend PowerStatus = properties.extended.instanceView.powerState.displayStatus
| extend env_tag = tags.Environment
| extend app_tag = tags.App
| extend description_tag = tags.Description
| extend AssetName_tag = tags.AssetName
| project tenantId,location, env_tag, app_tag, description_tag,AssetName_tag, resourceId,name, type, subscriptionName, subscriptionId, resourceGroup, isBackedUp, backupItemid, sku_2, publisher, offer, osType, osVersion, osName, PowerStatus, policy_name, lastBackup_status, protection_status, lastbackup, lastRecoveryPoint
                """

        exit_code, result_dict, logs = az(
            f"graph query -q '{query}' --first 1000")
        print(logs)
        return exit_code, result_dict

    def output_xlsx(self):
        name_dict = dict()
        type_dict = dict()
        location_dict = dict()
        rg_dict = dict()
        subscription_dict = dict()
        repo_tag_dict = dict()

        count = 0

        for resource in self.all_resource_list:
            name_dict[count] = resource.Name
            type_dict[count] = resource.Type
            location_dict[count] = resource.Location
            rg_dict[count] = resource.ResourceGroup
            subscription_dict[count] = resource.Subscription
            repo_tag_dict[count] = resource.Repo

            count += 1

        df = pd.DataFrame({"NAME": name_dict,
                           "TYPE": type_dict,
                           "LOCATION": location_dict,
                           "SUBSCRIPTION": subscription_dict,
                           "RESOURCEGROUP": rg_dict,
                           "REPO(TAG)": repo_tag_dict})

        print(df)

        # writer = pd.ExcelWriter(
        #     "files/resource_summary.xlsx", engine='xlsxwriter')
        # df.to_excel(writer, sheet_name="resourcelist", index=False)
        df.to_csv("files/resource_summary.csv", encoding='utf-8', index=False)
