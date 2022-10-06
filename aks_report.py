import json
from base import JsonCombiner, AKSReporter, AKSVersionProcessor


combined = JsonCombiner(folder_current='files', glob_current="sub_*.json",
                        folder_upgrades="files/", glob_upgrades="loc_*.json")

processor = AKSVersionProcessor()

reporter = AKSReporter(combined, processor)
reporter.make_report()


with open('files/report.json', "w") as f:

    json.dump(reporter.report, f)

reporter.output_xlsx()

print("Done")
