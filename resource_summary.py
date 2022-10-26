from summary_base import JsonCombiner, ResourceSummarizer

full_list = JsonCombiner(folder_path="./files")
ResourceSummarizer(combined_dict=full_list).output_xlsx()
