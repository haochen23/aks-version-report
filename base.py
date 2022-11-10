from abc import ABC, abstractmethod
import os
import json
import glob
import pandas as pd
from collections import OrderedDict


class DirectoryNotExist(Exception):

    pass


class ReportNotGenerated(Exception):

    pass


def versiontuple(v):
    return tuple(map(int, (v.split("."))))


class FileCombiner(ABC):

    current_versions = dict()
    upgrades = dict()

    @abstractmethod
    def _read_current(self) -> dict:
        pass

    @abstractmethod
    def _read_upgrades(self) -> dict:
        pass


class JsonCombiner(FileCombiner):

    def __init__(self,
                 folder_current: str = "",
                 glob_current: str = "",
                 folder_upgrades: str = "",
                 glob_upgrades: str = "") -> None:

        super().__init__()
        self.folder_current = folder_current
        self.glob_current = glob_current
        self.folder_upgrades = folder_upgrades
        self.glob_upgrades = glob_upgrades
        self.current_versions = self._read_current()
        self.upgrades = self._read_upgrades()

    def _read_current(self) -> dict:

        if not os.path.exists(self.folder_current):
            raise DirectoryNotExist(
                f"Path {self.folder_current} does not exist")

        for filename in glob.glob(os.path.join(self.folder_current, self.glob_current)):
            with open(filename) as f:
                # no time spend on slicing, hardcoded for now
                self.current_versions[filename[10:-5]] = json.load(f)

        return self.current_versions

    def _read_upgrades(self) -> dict:

        if not os.path.exists(self.folder_upgrades):
            raise DirectoryNotExist(
                f"Path {self.folder_upgrades} does not exist")

        for filename in glob.glob(os.path.join(self.folder_upgrades, self.glob_upgrades)):
            with open(filename) as f:
                # no time spend on slicing, hardcoded for now
                self.upgrades[filename[10:-5]] = json.load(f)
        return self.upgrades


class UpgradeStrategy(ABC):

    pass


class AKSUpgradeStrategy(UpgradeStrategy):

    @abstractmethod
    def get_upgrade_path(self, current_version, upgrades, is_outdated: bool):
        pass


class AggressiveAKSUpgradeStrategy(AKSUpgradeStrategy):

    def get_upgrade_path(self, current_version, upgrades, is_outdated: bool):
        upgrade_path = OrderedDict()
        version = current_version["k8sversion"]
        count = 1
        if is_outdated:
            version = upgrades["orchestrators"][0]["orchestratorVersion"]
            upgrade_path[f"Step {count}"] = version
            count += 1
        for orchestrator in upgrades["orchestrators"]:
            if versiontuple(version) < versiontuple(orchestrator["orchestratorVersion"]):
                version = orchestrator["orchestratorVersion"]
                upgrade_path[f"Step {count}"] = version

                count += 1
            if version == orchestrator["orchestratorVersion"]:
                if not orchestrator["upgrades"]:
                    # upgrade_path[f"Step {count}"] = "None Available"
                    break
                else:
                    upgrade_path[f"Step {count}"] = orchestrator["upgrades"][-1]["orchestratorVersion"]
                    version = orchestrator["upgrades"][-1]["orchestratorVersion"]
                    count += 1

        return upgrade_path, version


class VersionProcessor(ABC):

    @abstractmethod
    def get_next_upgrades(self, current_version, upgrades, upgrade_strategy: AKSUpgradeStrategy):
        pass

    @abstractmethod
    def is_outdated(self, current_version, upgrades) -> bool:
        pass

# class AKSUpgrades:
#     def __init__(self, upgrades_dict: dict) -> None:


class AKSVersionProcessor(VersionProcessor):

    def get_next_upgrades(self, current_version, upgrades, upgrade_strategy: AKSUpgradeStrategy):
        version_outdated = self.is_outdated(current_version, upgrades)

        upgrade_path, latest_GA_version = upgrade_strategy.get_upgrade_path(
            current_version, upgrades, is_outdated=version_outdated)
        is_latest = False

        if len(upgrade_path) <= 1:
            is_latest = True
        return version_outdated, json.dumps(upgrade_path, indent=4), is_latest, latest_GA_version

    def is_outdated(self, current_version, upgrades) -> bool:
        return versiontuple(current_version.get('k8sversion')) < versiontuple(upgrades["orchestrators"][0]["orchestratorVersion"])


class Reporter(ABC):

    def __init__(self, combined: FileCombiner, version_processor: VersionProcessor) -> None:
        super().__init__()
        self.combined = combined
        self.report = None
        self.version_processor = version_processor

    @abstractmethod
    def make_report(self, upgrade_strategy: AKSUpgradeStrategy):
        pass


class AKSReporter(Reporter):

    def make_report(self, upgrade_strategy):

        for subscription, clusters in self.combined.current_versions.items():
            if len(clusters) == 0:
                continue
            for current_version in clusters:
                upgrade = self.combined.upgrades[current_version.get(
                    "Location")]
                current_version["isOutdated"], \
                    current_version["nextAvailableUpgrades"], \
                    current_version["isLatest"], \
                    current_version["latestGAVersion"]\
                    = self.version_processor.get_next_upgrades(
                    current_version, upgrade, upgrade_strategy)
                current_version["subscription"] = subscription
        self.report = self.combined.current_versions

    def output_xlsx(self):
        if not self.report:
            raise ReportNotGenerated(
                "Generate report dict first by running make_report.")
        count = 0
        aks_dict = dict()
        subscription_dict = dict()
        current_version_dict = dict()
        is_outdated_dict = dict()
        is_latest_dict = dict()
        location_dict = dict()
        next_upgrades_dict = dict()
        latest_GA_dict = dict()

        for _, clusters in self.report.items():
            if len(clusters) == 0:
                continue
            for cluster in clusters:
                aks_dict[count] = cluster["Name"]
                subscription_dict[count] = cluster["subscription"]
                current_version_dict[count] = cluster["k8sversion"]
                is_outdated_dict[count] = cluster["isOutdated"]
                is_latest_dict[count] = cluster["isLatest"]
                location_dict[count] = cluster["Location"]
                next_upgrades_dict[count] = cluster["nextAvailableUpgrades"]
                latest_GA_dict[count] = cluster["latestGAVersion"]
                count += 1

        df = pd.DataFrame({"AKS_cluster": aks_dict,
                           "Subscription": subscription_dict,
                           "Current Version": current_version_dict,
                           "isOutdated": is_outdated_dict,
                           "isLatest": is_latest_dict,
                           "latest_GA_Version": latest_GA_dict,
                           "Location": location_dict,
                           "Upgrade to Latest": next_upgrades_dict})
        print(df)

        writer = pd.ExcelWriter("files/report.xlsx", engine='xlsxwriter')
        df.to_excel(writer, sheet_name="version_report", index=False)

        for location, upgrade in self.combined.upgrades.items():
            count = 0
            version_dict = dict()
            upgrades_dict = dict()
            for orchestrator in upgrade["orchestrators"]:
                upgrade_version_list = []
                version_dict[count] = orchestrator["orchestratorVersion"]
                if orchestrator["upgrades"]:
                    for up in orchestrator["upgrades"]:
                        upgrade_version_list.append(up["orchestratorVersion"])
                upgrades_dict[count] = upgrade_version_list
                count += 1

            df = pd.DataFrame({"KubernetesVersion": version_dict,
                               "Upgrades": upgrades_dict})
            df.to_excel(writer, sheet_name=f"{location}_upgrades", index=False)

        writer.close()
