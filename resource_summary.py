from summary_base import JsonCombiner, ResourceSummarizer

full_list = JsonCombiner(folder_path="./files")
resource_summary = ResourceSummarizer(combined_dict=full_list)
resource_summary.output_xlsx()
resource_summary.categorize_resources()
print("Done")
