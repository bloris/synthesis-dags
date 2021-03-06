"""
Before running add in weights name as a property of Params class.
"""

from time import strftime, gmtime
from os import path
import os

import numpy as np
import torch
from tqdm import tqdm

from syn_dags.script_utils import dogae_utils
from syn_dags.utils import misc
from syn_dags.data import synthesis_trees
from syn_dags.script_utils import opt_utils


class Params:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        self.weight_path = ""

        self.batch_size = 200
        self.num_batches = 100

        self.lambda_value = 10.  # see WAE paper, section 4

        time_run = strftime("%y-%m-%d_%H:%M:%S", gmtime())
        f_name_weights = path.splitext(path.basename(self.weight_path))[0]
        self.run_name = f"prior_samples_for_{f_name_weights}_done_{time_run}_"
        print(f"Run name is {self.run_name}")
        print(f"Checkpoint name is {self.weight_path}")


def main(params: Params):
    # Seeds
    rng = np.random.RandomState(564165)
    torch.manual_seed(15616)
    os.makedirs(path.join("out_preds", params.run_name))

    # Model!
    log_path = path.join("logs", f"reactions-{params.run_name}.log")
    model, __collate_func, *_ = dogae_utils.load_model(params.weight_path, params.device, params.reaction_predictor_server_address,
                                                       log_path)

    # Sample"
    out_tuple_trees = []
    all_z = []
    for batch in tqdm(range(params.num_batches), desc="sampling a batch"):
        out, z, _ = dogae_utils.sample_n_from_prior(model, params.batch_size, rng, return_extras=True)
        all_z.append(z.detach().cpu().numpy())
        out_tuple_trees.extend(out)
    all_z = np.concatenate(all_z, axis=0)

    # Write out!
    pickle_name = path.join("samples", f"out_trees_{params.run_name}.pick")
    root_smi_txt_name = path.join("samples", f"out_final_smi_{params.run_name}.txt")

    misc.to_pickle({'tuple_trees': out_tuple_trees,
                    'all_z': all_z}, pickle_name)
    print(f"Saving trees to {pickle_name}")

    smiles = [x[0] for x in out_tuple_trees]
    with open(root_smi_txt_name, 'w') as fo:
        fo.writelines('\n'.join(smiles))
    print(f"writing the SMILES out into {root_smi_txt_name}")


if __name__ == '__main__':
    main(Params())
    print("Done!")
