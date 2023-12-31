from pathlib import Path

from ..config.trainconfig import TrainConfig


class NLPTrainingConfig(TrainConfig):
    def __init__(
        self,
        seed: int = 0,
        gpu: bool = True,
        problem_type: str | None = None,
        dataset_name: str = "",
        train_file_path: Path | str | None = None,
        val_file_path: Path | str | None = None,
        test_file_path: Path | str | None = None,
        model_type: str = "",
        model_name: str = "",
        model_dir: str | None = None,
        metric: str = "loss",
        epochs: int = 0,
        train_batch_size: int = 0,
        infer_batch_size: int = 0,
        opt_type: str | None = None,
        opt_lr: float = 1e-4,
        opt_betas1: float = 0.9,
        opt_betas2: float = 0.999,
        opt_eps: float = 1e-8,
        opt_weight_decay: float = 0.01,
        sch_type: str | None = None,
        sch_warmup_min_lr: float = 0,
        sch_warmup_max_lr: float = 0,
        sch_warmup_num_steps: int = -1,
        sch_warmup_ratio_steps: float = -1,
        sch_total_num_steps: int = -1,
        sch_num_cycles: float = -1,
        save_dir: Path | str | None = None,
        run_dir: Path | str | None = None,
        early_stop: bool = False,
        patience: int = -1,
        continue_train_more_patience: bool = False,
        eval_every_half_epoch: bool = False,
        eval_step: int = 0,
        save_all_ckpts: bool = False,
        save_last_ckpt: bool = True,
        max_optimal_ckpt_num: int = 1,
        cache_dataset: bool = False,
        gradient_accumulation_steps: int = 1,
        gradient_clipping: float = 1.0,
        parallel_mode: str | None = None,
        ddp_timeout: int = 1800,
        fp16: bool = False,
        bf16: bool = False,
        dashboard: str | None = None,
        shuffle: bool | None = None,
        logging_steps: int = -1,
        torch_dtype: str = "auto",
        cut_input_from_output: bool = False,
        use_deepspeed_ckpt: bool = False,
        show_lr: bool = True,
        show_step: bool = True,
        max_length_input: int | None = None,
        max_length_label: int | None = None,
        max_length: int | None = 20,
        max_new_tokens: int | None = None,
        do_sample: bool = False,
        num_beams: int = 1,
        early_stopping: bool = False,
        use_cache: bool = True,
        top_k: int = 50,
        top_p: float = 1.0,
        temperature: float = 1.0,
        diversity_penalty: float = 0.0,
        repetition_penalty: float = 1.0,
        length_penalty: float = 1.0,
        padding_side: str = "right",
        **kwargs,
    ):
        super().__init__(
            seed,
            gpu,
            problem_type,
            dataset_name,
            train_file_path,
            val_file_path,
            test_file_path,
            model_type,
            model_name,
            model_dir,
            metric,
            epochs,
            train_batch_size,
            infer_batch_size,
            opt_type,
            opt_lr,
            opt_betas1,
            opt_betas2,
            opt_eps,
            opt_weight_decay,
            sch_type,
            sch_warmup_min_lr,
            sch_warmup_max_lr,
            sch_warmup_num_steps,
            sch_warmup_ratio_steps,
            sch_total_num_steps,
            sch_num_cycles,
            save_dir,
            run_dir,
            early_stop,
            patience,
            continue_train_more_patience,
            eval_every_half_epoch,
            eval_step,
            save_all_ckpts,
            save_last_ckpt,
            max_optimal_ckpt_num,
            cache_dataset,
            gradient_accumulation_steps,
            gradient_clipping,
            parallel_mode,
            ddp_timeout,
            fp16,
            bf16,
            dashboard,
            shuffle,
            logging_steps,
            torch_dtype,
            cut_input_from_output,
            use_deepspeed_ckpt,
            show_lr,
            show_step,
            **kwargs,
        )
        self.padding_side = padding_side
        self.max_length_input = max_length_input
        self.max_length_label = max_length_label

        self.do_sample = do_sample
        self.num_beams = num_beams
        self.early_stopping = early_stopping
        self.use_cache = use_cache
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.diversity_penalty = diversity_penalty
        self.repetition_penalty = repetition_penalty
        self.length_penalty = length_penalty
        self.max_new_tokens = max_new_tokens
        self.max_length = max_length

        # self.pretrained_model_path = pretrained_model_path

    @property
    def generate_kwargs(self):
        ret = {
            "do_sample": self.do_sample,
            "num_beams": self.num_beams,
            "early_stopping": self.early_stopping,
            "use_cache": self.use_cache,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "diversity_penalty": self.diversity_penalty,
            "repetition_penalty": self.repetition_penalty,
            "length_penalty": self.length_penalty,
        }
        # 如果设置了`max_new_tokens`就不设置`max_length`, 防止 transformer 的 warning
        if self.max_new_tokens is not None:
            ret["max_new_tokens"] = self.max_new_tokens
        else:
            ret["max_length"] = self.max_length
        return ret

    # todo 当前只会覆盖 d 中出现的参数, 正常应该还要把 d 中没出现的参数置为默认值
    @generate_kwargs.setter
    def generate_kwargs(self, d: dict):
        # if set(d.keys()).issubset(set(self.generate_kwargs.keys())):
        if not isinstance(d, dict):
            raise ValueError(f"`generate_kwargs` must be a dict but got '{type(d)}'")
        for key, value in d.items():
            if key in self.generate_kwargs:
                setattr(self, key, value)
            else:
                raise KeyError(f"Invalid key for generate keyword arguments: {key}")

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
