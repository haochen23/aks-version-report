from abc import ABC, abstractmethod
from ast import Sub
from importlib import resources
import os
import json
import glob
from urllib import response
import pandas as pd
from collections import OrderedDict
from az.cli import az
from typing import List
import requests
from regex import W
from logger import logger, line

from data_model import Resource, VMResource, SQLVMResource, automation_account_map


class VirutalMachineOSTypeError(Exception):
    pass


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


class ResourceSummarizer:

    def __init__(self, combined_dict: JsonCombiner) -> None:
        self.subscriptions_list = set(
            [resource["Subscription"] for resource in combined_dict.resources])
        self.alerts_list = []

        self._get_alert_list()

        self.all_dsc_status = []

        combined_dict = self._update_resource_alert(combined_dict)
        self.all_resource_list = [
            Resource(**resource) for resource in combined_dict.resources]

        self.windows_vms: List(VMResource) = []
        self.linux_vms: List(VMResource) = []
        self.sql_vms = []
        self.sql_mi = []
        self.aks = []
        self.azure_sql = []

        self.backup_query_exit, self.backup_status = self._get_backup_status()

    def _update_resource_alert(self, combined_dict: JsonCombiner):
        for resource in combined_dict.resources:
            resource["alerts"] = []
            for alert in self.alerts_list:
                for scope in alert["scopes"]:
                    if resource["Name"] == scope.split('/')[-1]:
                        resource["alerts"].append(alert)
            resource["alerts_count"] = len(resource["alerts"])
        return combined_dict

    def _get_dsc_status(self):
        exit_code, result_dict, logs = az(
            f'account get-access-token --tenant {os.getenv("TENANT_ID")}')

        for subscriptionId, auto_accounts in automation_account_map.items():
            for rg, accounts in auto_accounts.items():
                for account in accounts:
                    r = requests.get(f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{rg}/providers/Microsoft.Automation/automationAccounts/{account}/nodes?api-version=2019-06-01", headers={
                                     f"Authorization": f"Bearer {result_dict['accessToken']}"})

                    self.all_dsc_status.extend(r.json()["value"])

    def categorize_resources(self):
        for resource in self.all_resource_list:
            if resource.Type == "Microsoft.Compute/virtualMachines":
                for backup_query_item in self.backup_status["data"]:
                    if resource.Name == backup_query_item.get("name") and (backup_query_item.get("backupItemid") == "iaasresourcecontainerv2" or backup_query_item.get("isBackedUp")):
                        if backup_query_item["osType"].lower() == "windows":
                            self.windows_vms.append(VMResource(Name=resource.Name, Location=resource.Location,
                                                               Id=resource.Id,
                                                               alerts=resource.alerts, alerts_count=resource.alerts_count,
                                                               Type=resource.Type, Repo=resource.Repo, ResourceGroup=resource.ResourceGroup,
                                                               Subscription=resource.Subscription, osType=backup_query_item[
                                                                   "osType"],
                                                               osName=backup_query_item[
                                                                   "osName"], osVersion=backup_query_item["osVersion"],
                                                               isBackedUp=backup_query_item[
                                                                   "isBackedUp"], lastbackup=backup_query_item["lastbackup"],
                                                               lastBackup_status=backup_query_item["lastBackup_status"],
                                                               lastRecoveryPoint=backup_query_item["lastRecoveryPoint"],
                                                               protection_status=backup_query_item["protection_status"],
                                                               policy_name=backup_query_item["policy_name"],
                                                               backupItemid=backup_query_item["backupItemid"],
                                                               PowerStatus=backup_query_item["PowerStatus"],
                                                               offer=backup_query_item[
                                                                   "offer"], publisher=backup_query_item["publisher"],
                                                               sku=backup_query_item["sku_2"],
                                                               RSV=backup_query_item["backupItemid"].split("/")[4]))
                            break
                        elif backup_query_item["osType"].lower() == "linux":
                            self.linux_vms.append(VMResource(Name=resource.Name, Location=resource.Location,
                                                             Id=resource.Id,
                                                             alerts=resource.alerts, alerts_count=resource.alerts_count,
                                                             Type=resource.Type, Repo=resource.Repo, ResourceGroup=resource.ResourceGroup,
                                                             Subscription=resource.Subscription, osType=backup_query_item[
                                                                 "osType"],
                                                             osName=backup_query_item[
                                                                 "osName"], osVersion=backup_query_item["osVersion"],
                                                             isBackedUp=backup_query_item[
                                                                 "isBackedUp"], lastbackup=backup_query_item["lastbackup"],
                                                             lastBackup_status=backup_query_item["lastBackup_status"],
                                                             lastRecoveryPoint=backup_query_item["lastRecoveryPoint"],
                                                             protection_status=backup_query_item["protection_status"],
                                                             policy_name=backup_query_item["policy_name"],
                                                             backupItemid=backup_query_item["backupItemid"],
                                                             PowerStatus=backup_query_item["PowerStatus"],
                                                             offer=backup_query_item["offer"], publisher=backup_query_item["publisher"],
                                                             sku=backup_query_item["sku_2"],
                                                             RSV=backup_query_item["backupItemid"].split("/")[4]))
                            break
                        else:
                            raise VirutalMachineOSTypeError(
                                backup_query_item["osType"])
            elif resource.Type == "Microsoft.SqlVirtualMachine/SqlVirtualMachines":
                for backup_query_item in self.backup_status["data"]:
                    if resource.Name == backup_query_item.get("name"):

                        self.sql_vms.append(SQLVMResource(Location=resource.Location, Name=resource.Name,
                                                          Repo=resource.Repo, Type=resource.Type, ResourceGroup=resource.ResourceGroup,
                                                          Subscription=resource.Subscription, Id=resource.Id, alerts=resource.alerts,
                                                          alerts_count=resource.alerts_count, policy_name=backup_query_item[
                                                              "policy_name"],
                                                          protection_status=backup_query_item["protection_status"],
                                                          lastbackup=backup_query_item["lastbackup"],
                                                          lastBackup_status=backup_query_item["lastBackup_status"],
                                                          RSV=backup_query_item["backupItemid"].split(
                                                              '/')[4],
                                                          isBackedUp=backup_query_item["isBackedUp"],
                                                          vmSize=backup_query_item.get("properties").get("hardwareProfile").get('vmSize')))
                        break
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
// | project tenantId,location, env_tag, app_tag, description_tag,AssetName_tag, resourceId,name, type, subscriptionId, resourceGroup, isBackedUp, backupItemid, sku_2, publisher, offer, osType, osVersion, osName, PowerStatus, policy_name, lastBackup_status, protection_status, lastbackup, lastRecoveryPoint
                """

        exit_code, result_dict, logs = az(
            f"graph query -q '{query}' --first 1000")
        print(logs)
        return exit_code, result_dict

    def _get_alert_list(self):
        for subscription in self.subscriptions_list:
            exit_code, result_dict, logs = az(
                f"monitor metrics alert list --subscription {subscription}")
            self.alerts_list.extend(result_dict)

    def check_windows_vms(self):
        logger.info(line)
        logger.info("Processing Windoes VMs")
        if len(self.windows_vms) < 1:
            logger.info("No windows VMs in the listed resource groups")
            return

        self._get_dsc_status()
        for vm in self.windows_vms:
            logger.info(f"Processsing {vm.Name}")
            exit_code, result_dict, logs = az(
                f"vm show -n '{vm.Name}' -g {vm.ResourceGroup} --subscription {vm.Subscription}")

            vm.Size = result_dict.get("hardwareProfile").get("vmSize")
            vm.extentions = result_dict.get("resources")
            vm.dsc_status = None
            vm.dsc_compliant = None
            for dsc_node in self.all_dsc_status:
                if dsc_node["id"].split('/')[-1] == vm.Name:
                    vm.dsc_status = dsc_node["properties"]['status']
                    vm.dsc_compliant = dsc_node["properties"]['status'] == 'Compliant'

    def check_linux_vms(self):

        logger.info(line)
        logger.info("Processing Linux VMs")
        if len(self.linux_vms) < 1:
            logger.info("No Linux VMs in the listed resource groups")
            return

        for vm in self.linux_vms:
            logger.info(f"Processing {vm.Name}")
            exit_code, result_dict, logs = az(
                f"vm show -n '{vm.Name}' -g {vm.ResourceGroup} --subscription {vm.Subscription}")

            vm.Size = result_dict.get("hardwareProfile").get("vmSize")
            vm.extentions = result_dict.get("resources")
            # dcr linux_to_sec
            vm.dcr_sec = None
            # dcr linux_to_shd
            vm.dcr_shd = None

            exit_code, result_dict, logs = az(
                f"monitor data-collection rule association list --resource {vm.Id}")

            if not result_dict:
                return
            for dcr in result_dict:
                if not dcr.get("dataCollectionRuleId"):
                    continue
                if dcr.get("dataCollectionRuleId").split('/')[-1].lower() == 'linux-to-sec':
                    vm.dcr_sec = True
                elif dcr.get("dataCollectionRuleId").split('/')[-1].lower() == 'linux-to-shd':
                    vm.dcr_shd = True
                else:
                    logger.warn(
                        f"{vm.Name} not connected to either 'linux-to-sec` or 'linux-to-shd'.")

    # def check_sql_vms(self):

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
