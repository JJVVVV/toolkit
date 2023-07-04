import copy
import glob
import json
import os
import shutil
from functools import reduce
from heapq import nlargest
from pathlib import Path
from typing import Any, Dict, List, Tuple

from transformers import PreTrainedModel, PreTrainedTokenizer, PreTrainedTokenizerFast

from ..config.trainconfig import TrainConfig
from ..logger import _getLogger
from ..utils.misc import search_file
from .metricdict import MetricDict

logger = _getLogger(__name__)

WATCHDOG_DATA_NAME = "watchdog_data.json"


class WatchDog:
    """Early stops the training if validation loss doesn't improve after a given patience."""

    def __init__(self, patience: int = 5, metric: str = "acc"):
        """
        Args:
            patience (int): How long to wait after last time validation loss improved.
                            上次验证集损失值改善后等待几个epoch
                            Default: 7
            verbose (bool): If True, prints a message for each validation loss improvement.
                            如果是True, 为每个验证集损失值改善打印一条信息
                            Default: False
            delta (float): Minimum change in the monitored quantity to qualify as an improvement.
                            监测数量的最小变化，以符合改进的要求
                            Default: 0
        """
        self.patience = patience
        self.counter = 0

        self.need_to_stop = False
        self.best_checkpoint = None

        self.metric_used_to_comp = metric
        MetricDict.metric_used_to_comp = self.metric_used_to_comp  # ? loss, acc,  f1
        # * 保证 MetricDict 中的值越大越好
        match metric:
            case "loss":
                self.scale = -1
            case _:
                self.scale = 1

        MetricDict.scale = self.scale

        self.optimal_dev_metrics_dict = None
        self.optimal_test_metrics_dict = None
        self.cheat_test_metrics_dict = None

    def __call__(
        self,
        dev_metrics_dict: MetricDict,
        test_metrics_dict: MetricDict | None,
        curCheckpoint: int,
        curStep: int,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast,
        configs: TrainConfig,
    ):
        if self.optimal_dev_metrics_dict is None:
            self.best_checkpoint = curCheckpoint
            self.optimal_dev_metrics_dict = MetricDict(dev_metrics_dict)
            if test_metrics_dict is not None:
                self.optimal_test_metrics_dict = MetricDict(test_metrics_dict)
            self.save_checkpoint(model, tokenizer, configs)
        elif dev_metrics_dict > self.optimal_dev_metrics_dict:
            self.best_checkpoint = curCheckpoint
            self.optimal_dev_metrics_dict.update(dev_metrics_dict)
            if test_metrics_dict is not None:
                self.optimal_test_metrics_dict.update(test_metrics_dict)
            self.save_checkpoint(model, tokenizer, configs)
            self.counter = 0
        else:
            self.counter += 1
            logger.debug(f"EarlyStopping counter: {self.counter}/{self.patience}")
            if self.counter >= self.patience:
                self.need_to_stop = True

        if test_metrics_dict is not None:
            if self.cheat_test_metrics_dict is None:
                self.cheat_test_metrics_dict = MetricDict(test_metrics_dict)
            elif test_metrics_dict > self.cheat_test_metrics_dict:
                self.cheat_test_metrics_dict.update(test_metrics_dict)
        logger.debug(f"EarlyStopping: {self.optimal_dev_metrics_dict[self.metric_used_to_comp]} {self.counter}/{self.patience}")

    def save_checkpoint(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast, configs: TrainConfig):
        output_dir = Path(configs.checkpoints_dir, "best_checkpoint")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir()

        logger.debug(f"Saving the optimal model and tokenizer to {output_dir}.")
        model_to_save = model.module if hasattr(model, "module") else model
        model_to_save.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        configs.save(output_dir)
        logger.debug(f"Save successfully.")

    def save(self, save_dir: Path | str, json_file_name: str = WATCHDOG_DATA_NAME, silence=True, **kwargs):
        if isinstance(save_dir, str):
            save_dir = Path(save_dir)
        if save_dir.is_file():
            raise AssertionError(f"Provided path ({save_dir}) should be a directory, not a file")
        save_dir.mkdir(parents=True, exist_ok=True)
        json_file_path = save_dir / json_file_name

        self.to_json_file(json_file_path)
        if not silence:
            logger.debug(f"Earlystopping data saved in {json_file_path}")

    @classmethod
    def load(cls, json_file_dir_or_path: Path | str, json_file_name: str = WATCHDOG_DATA_NAME, silence=True, **kwargs) -> "WatchDog":
        if isinstance(json_file_dir_or_path, str):
            json_file_dir_or_path = Path(json_file_dir_or_path)

        if json_file_dir_or_path.is_file():
            json_file_path = json_file_dir_or_path
        else:
            json_file_path = json_file_dir_or_path / json_file_name
        # Load config dict
        try:
            attributes_dict = cls._dict_from_json_file(json_file_path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise EnvironmentError(f"It looks like the config file at '{json_file_path}' is not a valid JSON file.")
        if not silence:
            logger.debug(f"Loading earlystopping data file from: {json_file_path}")
        attributes_dict.update(kwargs)
        early_stopping = cls.from_dict(attributes_dict)
        MetricDict.scale = early_stopping.scale
        MetricDict.metric_used_to_comp = early_stopping.metric_used_to_comp
        return early_stopping

    @staticmethod
    def _dict_from_json_file(json_file: Path | str) -> Dict:
        with open(json_file, "r", encoding="utf-8") as reader:
            text = reader.read()
        attributes_dict = json.loads(text)
        for key, value in attributes_dict.items():
            if isinstance(value, dict):
                attributes_dict[key] = MetricDict(value)
        return attributes_dict

    @classmethod
    def from_dict(cls, attributes_dict: Dict[str, Any]) -> "WatchDog":
        early_stopping = cls()
        early_stopping._update(attributes_dict)
        return early_stopping

    def _update(self, attributes_dict: Dict[str, Any]):
        for key, value in attributes_dict.items():
            setattr(self, key, value)

    def to_json_file(self, json_file_path: Path | str):
        with open(json_file_path, "w", encoding="utf-8") as writer:
            writer.write(self.to_json_string())

    def to_json_string(self) -> str:
        attributes_dict = self.to_dict()
        for key, value in attributes_dict.items():
            if isinstance(value, MetricDict):
                attributes_dict[key] = dict(value)
        return json.dumps(attributes_dict, indent=2, sort_keys=False) + "\n"

    def to_dict(self) -> Dict[str, Any]:
        output = copy.deepcopy(self.__dict__)
        return output

    @classmethod
    def metric_dicts_from_diff_seeds(
        cls, seeds_dir: Path | str, json_file_name: str = WATCHDOG_DATA_NAME
    ) -> Tuple[List[MetricDict], List[MetricDict], List[MetricDict]]:
        """
        Get a list of validation metricdict, test metricdict and cheat test metricdict from different seed.
        """
        seed_dirs = glob.glob(seeds_dir + "/*")
        success = 0
        dev_metrics_dicts = []
        test_metrics_dicts = []
        cheat_metrics_dicts = []
        for seed_dir in seed_dirs:
            watchdog_data_path = search_file(seed_dir, json_file_name)
            if watchdog_data_path and "checkpoint-" not in watchdog_data_path[0]:
                earlyStopping = cls.load(watchdog_data_path[0], silence=True)
                dev_metrics_dicts.append(earlyStopping.optimal_dev_metrics_dict)
                test_metrics_dicts.append(earlyStopping.optimal_test_metrics_dict)
                cheat_metrics_dicts.append(earlyStopping.cheat_test_metrics_dict)
                success += 1
            else:
                logger.debug(seed_dir)
        logger.info(f"success/total: {success}/{len(seed_dirs)}")
        return dev_metrics_dicts, test_metrics_dicts, cheat_metrics_dicts
