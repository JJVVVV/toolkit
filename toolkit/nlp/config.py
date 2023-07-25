from pathlib import Path

from ..config.trainconfig import TrainConfig, logger


class NLPTrainingConfig(TrainConfig):
    def __init__(
        self,
        dataset_name: str = "",
        metric: str = "Loss",
        epochs: int = 3,
        batch_size: int = 16,
        optimizer: str | None = None,
        lr_scheduler: str | None = None,
        learning_rate: float = 0.001,
        checkpoints_dir: Path | str | None = None,
        batch_size_infer: int = None,
        train_file_path: Path | str | None = None,
        val_file_path: Path | str | None = None,
        test_file_path: Path | str | None = None,
        model_type: str = "",
        model_name: str = "",
        problem_type: str | None = None,
        seed: int = 0,
        early_stop: bool = False,
        patience: int = -1,
        continue_train_more_patience: bool = False,
        test_in_epoch: bool = False,
        weight_decay: float = 0.01,
        epsilon: float = 1e-8,
        accumulate_step: int = 1,
        warmup: bool = False,
        warmup_ratio: float = -1,
        fp16: bool = False,
        dashboard: str | None = None,
        max_length_input: int | None = None,
        max_length_label: int | None = None,
        pretrained_model_path: Path | str = "",
        padding_side: str = "right",
        **kwargs,
    ):
        super().__init__(
            dataset_name,
            metric,
            epochs,
            batch_size,
            optimizer,
            lr_scheduler,
            learning_rate,
            checkpoints_dir,
            batch_size_infer,
            train_file_path,
            val_file_path,
            test_file_path,
            model_type,
            model_name,
            problem_type,
            seed,
            early_stop,
            patience,
            continue_train_more_patience,
            test_in_epoch,
            weight_decay,
            epsilon,
            accumulate_step,
            warmup,
            warmup_ratio,
            fp16,
            dashboard,
            **kwargs,
        )
        self.padding_side = padding_side
        self.max_length_input = max_length_input
        self.max_length_label = max_length_label
        self.pretrained_model_path = pretrained_model_path

        logger.info("Custom training parameters:")
        for key, value in kwargs.items():
            logger.info(f"{key}={value}")

    # def print_some_info(self):
    #     logger.debug("***** Some training information *****")
    #     logger.debug(f"  Batch size = {self.batch_size}")
    #     logger.debug(f"  Total epochs = {self.epochs:d}")
    #     logger.debug(f"  Steps per epoch = {stepsPerEpoch:d}")
    #     logger.debug(f"  Total steps = {totalSteps:d}")
    #     if self.warmup:
    #         logger.debug(f"  Warmup steps = {warmupSteps:d}")
    #     logger.debug(f"  Model type = {self.model_type}")
    #     logger.debug(f"  fp16: {self.fp16}\n")
