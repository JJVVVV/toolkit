import datetime
import os
import random
from typing import Tuple

import numpy as np
import torch
import torch.distributed as dist

from .. import toolkit_logger

# from ..logger import _getLogger

# logger = _getLogger(__name__)
# logger.addHandler(file_handlers[0])


def setup_seed(seed: int) -> None:
    """Set random seed"""
    local_rank = dist.get_rank() if dist.is_initialized() else 0
    world_size = dist.get_world_size() if dist.is_initialized() else 1
    # 如果读取数据的过程采用了随机预处理(如RandomCrop、RandomHorizontalFlip等)，那么对Python、Numpy的随机数生成器也需要设置种子。
    random.seed(seed)
    np.random.seed(seed)
    # 为了禁止hash随机化，使得实验可复现
    os.environ["PYTHONHASHSEED"] = str(seed)
    # torch中的随机种子
    torch.manual_seed(seed)  # 为CPU设置随机种子
    torch.cuda.manual_seed(seed)  # 为当前GPU设置随机种子
    # if you are using multi-GPU. 为所有GPU设置随机种子
    torch.cuda.manual_seed_all(seed)
    if local_rank == 0:
        toolkit_logger.info(f"seed={seed}")


def setup_parallel() -> Tuple[int, int]:
    """Initial parallel backend"""
    local_rank = int(os.environ.get("LOCAL_RANK", -1))
    world_size = int(os.environ.get("WORLD_SIZE", -1))
    if local_rank == 0:
        try:
            toolkit_logger.debug(f"NCCL_BLOCKING_WAIT={os.environ['NCCL_BLOCKING_WAIT']}")
        except:
            pass
        try:
            toolkit_logger.debug(f"NCCL_ASYNC_ERROR_HANDLING={os.environ['NCCL_ASYNC_ERROR_HANDLING']}")
        except:
            pass
    dist.init_process_group("nccl", timeout=datetime.timedelta(seconds=7200))
    torch.cuda.set_device(local_rank)

    return local_rank, world_size


# torch申请显存
def check_mem(cuda_device_id: int) -> Tuple[int, int]:
    """Get total and used memory (unit: `MB`) of GPU with the corresponding ID."""
    devices_info = os.popen('"/usr/bin/nvidia-smi" --query-gpu=memory.total,memory.used --format=csv,nounits,noheader').read().strip().split("\n")
    total, used = devices_info[int(cuda_device_id)].split(",")
    return int(total), int(used)


def allocate_gpu_memory(ratio=0.8) -> None:
    """Allocate GPU memory.\n
    Support multiple GPUs, but the GPU used by the current process must be specified by `torch.cuda.set_device(local_rank)`"""
    local_rank = dist.get_rank() if dist.is_initialized() else 0

    cuda_device_ids = os.environ["CUDA_VISIBLE_DEVICES"].split(",")
    cuda_device_ids = [cuda_device_id for cuda_device_id in cuda_device_ids if cuda_device_id]
    local_cuda_device_id = cuda_device_ids[local_rank]
    total, used = check_mem(local_cuda_device_id)
    block_mem = int((int(total) - int(used)) * ratio)
    x = torch.cuda.FloatTensor(256, 1024, block_mem)
    del x