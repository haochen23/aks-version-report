from summary_base import JsonCombiner, ResourceSummarizer
from summary_reporter import SummaryReporter
import logger
print(logger.logger)
logger.logger.error("fuck")

full_list = JsonCombiner(folder_path="./files")
resource_summary = ResourceSummarizer(combined_dict=full_list)
resource_summary.output_xlsx()
resource_summary.categorize_resources()
resource_summary.check_windows_vms()
resource_summary.check_linux_vms()

reporter = SummaryReporter(rs=resource_summary)
reporter.report()

print("Done")
