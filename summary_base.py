from abc import ABC, abstractmethod
from importlib import resources
import os
import json
import glob
import pandas as pd
from collections import OrderedDict


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
        self.resource_list = combined_dict.resources

    def output_xlsx(self):
        name_dict = dict()
        type_dict = dict()
        location_dict = dict()
        rg_dict = dict()
        subscription_dict = dict()
        repo_tag_dict = dict()

        count = 0

        for resource in self.resource_list:
            name_dict[count] = resource["Name"]
            type_dict[count] = resource["Type"]
            location_dict[count] = resource["Location"]
            rg_dict[count] = resource["ResourceGroup"]
            subscription_dict[count] = resource["Subscription"]
            repo_tag_dict[count] = resource["Repo"]

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
