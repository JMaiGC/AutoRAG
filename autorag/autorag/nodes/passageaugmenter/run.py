import logging
import os
import pathlib
from typing import List, Dict

import pandas as pd

from autorag.nodes.retrieval.run_util import evaluate_retrieval_node
from autorag.schema.metricinput import MetricInput
from autorag.strategy import measure_speed, filter_by_threshold, select_best
from autorag.utils.util import apply_recursive, to_list

logger = logging.getLogger("AutoRAG")


def run_passage_augmenter_node(
	modules: List,
	module_params: List[Dict],
	previous_result: pd.DataFrame,
	node_line_dir: str,
	strategies: Dict,
) -> pd.DataFrame:
	if not os.path.exists(node_line_dir):
		os.makedirs(node_line_dir)
	project_dir = pathlib.PurePath(node_line_dir).parent.parent
	qa_df = pd.read_parquet(
		os.path.join(project_dir, "data", "qa.parquet"), engine="pyarrow"
	)
	retrieval_gt = qa_df["retrieval_gt"].tolist()
	retrieval_gt = apply_recursive(lambda x: str(x), to_list(retrieval_gt))

	results, execution_times = zip(
		*map(
			lambda task: measure_speed(
				task[0].run_evaluator,
				project_dir=project_dir,
				previous_result=previous_result,
				**task[1],
			),
			zip(modules, module_params),
		)
	)
	average_times = list(map(lambda x: x / len(results[0]), execution_times))
	metric_inputs = [
		MetricInput(retrieval_gt=ret_gt, query=query, generation_gt=gen_gt)
		for ret_gt, query, gen_gt in zip(
			retrieval_gt,
			previous_result["query"].tolist(),
			previous_result["generation_gt"].tolist(),
		)
	]

	# run metrics before filtering
	if strategies.get("metrics") is None:
		raise ValueError(
			"You must at least one metrics for passage_augmenter evaluation."
		)
	results = list(
		map(
			lambda x: evaluate_retrieval_node(
				x,
				metric_inputs,
				strategies.get("metrics"),
			),
			results,
		)
	)

	# save results to folder
	save_dir = os.path.join(node_line_dir, "passage_augmenter")  # node name
	if not os.path.exists(save_dir):
		os.makedirs(save_dir)
	filepaths = list(
		map(lambda x: os.path.join(save_dir, f"{x}.parquet"), range(len(modules)))
	)
	list(
		map(lambda x: x[0].to_parquet(x[1], index=False), zip(results, filepaths))
	)  # execute save to parquet
	filenames = list(map(lambda x: os.path.basename(x), filepaths))

	summary_df = pd.DataFrame(
		{
			"filename": filenames,
			"module_name": list(map(lambda module: module.__name__, modules)),
			"module_params": module_params,
			"execution_time": average_times,
			**{
				f"passage_augmenter_{metric}": list(
					map(lambda result: result[metric].mean(), results)
				)
				for metric in strategies.get("metrics")
			},
		}
	)

	# filter by strategies
	if strategies.get("speed_threshold") is not None:
		results, filenames = filter_by_threshold(
			results, average_times, strategies["speed_threshold"], filenames
		)
	selected_result, selected_filename = select_best(
		results,
		strategies.get("metrics"),
		filenames,
		strategies.get("strategy", "mean"),
	)
	# change metric name columns to passage_augmenter_metric_name
	selected_result = selected_result.rename(
		columns={
			metric_name: f"passage_augmenter_{metric_name}"
			for metric_name in strategies["metrics"]
		}
	)
	# drop retrieval result columns in previous_result
	previous_result = previous_result.drop(
		columns=["retrieved_contents", "retrieved_ids", "retrieve_scores"]
	)
	best_result = pd.concat([previous_result, selected_result], axis=1)

	# add 'is_best' column to summary file
	summary_df["is_best"] = summary_df["filename"] == selected_filename

	# save files
	summary_df.to_csv(os.path.join(save_dir, "summary.csv"), index=False)
	best_result.to_parquet(
		os.path.join(
			save_dir, f"best_{os.path.splitext(selected_filename)[0]}.parquet"
		),
		index=False,
	)
	return best_result
