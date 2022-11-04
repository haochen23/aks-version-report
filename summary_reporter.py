from data_model import VMResource, Resource
from summary_base import ResourceSummarizer
from logger import logger, line

line2 = "****************************************************"


class SummaryReporter:

    def __init__(self, rs: ResourceSummarizer) -> None:
        self.rs = rs

    def report_windows_vms(self):
        if len(self.rs.windows_vms) < 1:
            return
        logger.info(line)
        logger.info("Reporting windows VMs to log file")
        logger.info(line)

        for vm in self.rs.windows_vms:
            self._report_vm_general(vm=vm)

            logger.info(f'DSC Status: {vm.dsc_status}')
            logger.info(f'DSC Complaint: {vm.dsc_compliant}')

    def report_linux_vms(self):
        if len(self.rs.linux_vms) < 1:
            return
        logger.info(line)
        logger.info("Reporting Linux VMs to log file")
        logger.info(line)

        for vm in self.rs.linux_vms:
            self._report_vm_general(vm=vm)

            logger.info(f'DCR linux-to-sec: {vm.dcr_sec}')
            logger.info(f'DCR linux-to-shd: {vm.dcr_shd}')

    def report_sql_vms(self):
        if len(self.rs.sql_vms) < 1:
            return
        logger.info(line)
        logger.info("Reporting SQL VMs to log file")
        logger.info(line)

        for vm in self.rs.sql_vms:
            logger.info(line2)
            logger.info(f"Name: {vm.Name}")
            logger.info(f"vmSize: {vm.vmSize}")
            logger.info(f'Resrouce Group: {vm.ResourceGroup}')
            logger.info(f'Subscription: {vm.Subscription}')

            logger.info(f'Backup:')
            logger.info(f'      Backup Policy: {vm.policy_name}')
            logger.info(f"      RSV: {vm.RSV}")
            logger.info(f'      lastBackupStatus: {vm.lastBackup_status}')
            logger.info(
                f'      isBackedup: {"Yes" if vm.isBackedUp > 0 else "No"}')
            logger.info(f'      Protection Status: {vm.protection_status}')

            logger.info(
                f'Alert Setup: {"Ok" if vm.alerts_count > 0 or (vm.Subscription != ("AU-SHARED-001" or "AU-PROD-001")) else "No good"}')
            logger.info(f'Alerts count: {vm.alerts_count}')

    def report_azure_sql(self):
        if len(self.rs.azure_sql) < 1:
            return
        logger.info(line)
        logger.info("Reporting Azure SQL to log file")
        logger.info(line)
        for azure_sql in self.rs.azure_sql:
            self._report_resource_general(resource=azure_sql)

    def report_sql_mi(self):
        if len(self.rs.sql_mi) < 1:
            return
        logger.info(line)
        logger.info("Reporting SQL MI to log file")
        logger.info(line)
        for sql_mi in self.rs.sql_mi:
            self._report_resource_general(resource=sql_mi)

    def report_aks(self):
        if len(self.rs.aks) < 1:
            return
        logger.info(line)
        logger.info("Reporting AKS to log file")
        logger.info(line)
        for aks in self.rs.aks:
            self._report_resource_general(resource=aks)

    def report(self):
        self.report_windows_vms()
        self.report_linux_vms()
        self.report_sql_vms()
        self.report_sql_mi()
        self.report_azure_sql()
        self.report_aks()

    def _report_resource_general(self, resource: Resource):
        logger.info(line2)
        logger.info(f"Name: {resource.Name}")
        logger.info(f'Resrouce Group: {resource.ResourceGroup}')
        logger.info(f'Subscription: {resource.Subscription}')
        logger.info(f'Type: {resource.Type}')

    def _report_vm_general(self, vm: VMResource):
        logger.info(line2)
        self._report_resource_general(resource=vm)

        logger.info(f"Power Status: {vm.PowerStatus}")
        logger.info(f'OS: {vm.osName}')
        logger.info(f'Backup:')
        logger.info(f'      Backup Policy: {vm.policy_name}')
        logger.info(f"      RSV: {vm.RSV}")
        logger.info(f'      lastBackupStatus: {vm.lastBackup_status}')
        logger.info(
            f'      isBackedup: {"Yes" if vm.isBackedUp > 0 else "No"}')
        logger.info(f'      Protection Status: {vm.protection_status}')

        logger.info(
            f'Alert Setup: {"Ok" if vm.alerts_count > 0 or (vm.Subscription != ("AU-SHARED-001" or "AU-PROD-001")) else "No good"}')
        logger.info(f'Alerts count: {vm.alerts_count}')

        logger.info("Extensions:")
        for extension in vm.extentions:
            logger.info(
                f'   {extension["name"]}: {extension["provisioningState"]}')
