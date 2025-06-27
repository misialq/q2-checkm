# ----------------------------------------------------------------------------
# Copyright (c) 2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import subprocess
from collections import defaultdict
from typing import Dict, List, Mapping


def run_command(cmd, env=None, verbose=True):
    if verbose:
        print(
            "Running external command line application(s). This may print "
            "messages to stdout and/or stderr."
        )
        print(
            "The command(s) being run are below. These commands cannot "
            "be manually re-run as they will depend on temporary files that "
            "no longer exist."
        )
    if verbose:
        print("\nCommand:", end=" ")
        print(" ".join(cmd), end="\n\n")
    if env:
        subprocess.run(cmd, env=env, check=True)
    else:
        subprocess.run(cmd, check=True)


def _process_common_input_params(processing_func, params: dict) -> List[str]:
    """Converts provided arguments and their values.

    Conversion is entirely dependent on the passed 'processing_func'
    that processes individual arguments. The output is a list of
    parameters with their values that can be directly passed to the
    respective command.

    Arguments without any value are skipped.
    Any other argument is processed using the 'processing_func' and
    appended to the final list.

    Args:
        processing_func: Function to be used for formatting a single argument.
        params (dict): Dictionary of parameter: value pairs to be processed.

    Returns:
        processed_args (list): List of processed arguments and their values.

    """
    processed_args = []
    for arg_key, arg_val in params.items():
        # bool is a subclass of int so to only reject ints we need to do:
        if type(arg_val) is not int and not arg_val:
            continue
        else:
            processed_args.extend(processing_func(arg_key, arg_val))
    return processed_args


def _process_checkm_arg(arg_key, arg_val):
    """Creates a list with argument and its value to be consumed by CheckM.

    Argument names will be converted to command line parameters by
    appending a '--' prefix and concatenating words separated by a '_',
    e.g.: 'some_parameter_x' -> '--someParameterX'.

    Args:
        arg_key (str): Argument name.
        arg_val: Argument value.

    Returns:
        [converted_arg, arg_value]: List containing a prepared command line
            parameter and, optionally, its value.
    """
    if isinstance(arg_val, bool) and arg_val:
        return [f"--{arg_key}"]
    else:
        return [f"--{arg_key}", str(arg_val)]


def _get_plots_per_sample(
    all_plots: Mapping[str, Mapping[str, str]],
) -> Dict[str, Dict[str, str]]:
    """Converts mapping of different plot types-to-samples-to-plot paths into
        a new mapping of samples-to-plot types-to-plot paths.

    Args:
        all_plots (Mapping[str, Mapping[str, str]]): Dictionary containing plot
            paths per sample per plot type.

    Returns:
        Dict[str, Dict[str, str]]: Dictionary containing a new mapping of plot
            paths per plot type per sample.
    """
    # check if all plot types have the same count of samples
    all_samples = [set(k.keys()) for k in all_plots.values()]
    if not all([x == all_samples[0] for x in all_samples]):
        raise ValueError(
            "All plot types need to have the same set of samples. "
            f"Sample counts were: "
            f"{[len(k.keys()) for k in all_plots.values()]}."
        )

    plots_per_sample = defaultdict(dict)
    for key, val in all_plots.items():
        for subkey, subval in val.items():
            plots_per_sample[subkey][key] = subval
    return plots_per_sample
