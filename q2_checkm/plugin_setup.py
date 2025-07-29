# ----------------------------------------------------------------------------
# Copyright (c) 2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from q2_types.per_sample_sequences import MAGs
from q2_types.sample_data import SampleData
from qiime2.core.type import Bool, Float, Int, Range, Str
from qiime2.plugin import Citations, Plugin
import pandas as pd
import qiime2

import q2_checkm
from q2_checkm import __version__
from q2_checkm.checkm2 import (
    CheckM2Results,
    CheckM2ResultsFormat,
    CheckM2ResultsDirectoryFormat,
    quality_control
)
from q2_checkm.checkm2._transformers import (
    _checkm2_results_format_to_dataframe,
    _dataframe_to_checkm2_results_format,
    _checkm2_results_directory_to_dataframe,
    _checkm2_results_to_metadata
)

citations = Citations.load("citations.bib", package="q2_checkm")

plugin = Plugin(
    name="checkm",
    version=__version__,
    website="https://github.com/bokulich-lab/q2-checkm",
    package="q2_checkm",
    description="QIIME 2 plugin for (meta)genome quality assessment using CheckM.",
    short_description="QIIME 2 plugin for genome QC using CheckM.",
)

checkm_params = {
    "db_path": Str,
    "reduced_tree": Bool,
    "unique": Int % Range(1, None),
    "multi": Int % Range(1, None),
    "force_domain": Bool,
    "no_refinement": Bool,
    "individual_markers": Bool,
    "skip_adj_correction": Bool,
    "skip_pseudogene_correction": Bool,
    "aai_strain": Float % Range(0, 1),
    "ignore_thresholds": Bool,
    "e_value": Float % Range(0, 1),
    "length": Float % Range(0, 1),
    "threads": Int % Range(1, None),
    "pplacer_threads": Int % Range(1, None),
}

# fmt: off
checkm_param_descriptions = {
    "db_path": "Path to the database required by CheckM. For more details see: "
               "https://github.com/Ecogenomics/CheckM/wiki/Installation#"
               "required-reference-data.",
    "reduced_tree": "Use reduced tree (requires <16GB of memory) for "
                    "determining lineage of each bin.",
    "unique": "Minimum number of unique phylogenetic markers required to use "
              "lineage-specific marker set. Default: 10.",
    "multi": "Maximum number of multi-copy phylogenetic markers before "
             "defaulting to domain-level marker set. Default: 10.",
    "force_domain": "Use domain-level sets for all bins.",
    "no_refinement": "Do not perform lineage-specific marker set refinement.",
    "individual_markers": "Treat marker as independent "
                          "(i.e., ignore co-located set structure).",
    "skip_adj_correction": "Do not exclude adjacent marker genes when "
                           "estimating contamination.",
    "skip_pseudogene_correction": "Skip identification and filtering of pseudogenes.",
    "aai_strain": "AAI threshold used to identify strain heterogeneity. Default: 0.9.",
    "ignore_thresholds": "Ignore model-specific score thresholds.",
    "e_value": "E-value cut off. Default: 1e-10.",
    "length": "Percent overlap between target and query. Default: 0.7.",
    "threads": "Number of threads. Default: 1.",
    "pplacer_threads": "Number of threads used by pplacer (memory usage increases "
                       "linearly with additional threads). Default: 1."
}
# fmt: on

# Register CheckM2 semantic types and formats
plugin.register_semantic_types(CheckM2Results)
plugin.register_formats(CheckM2ResultsFormat, CheckM2ResultsDirectoryFormat)
plugin.register_semantic_type_to_format(
    CheckM2Results,
    artifact_format=CheckM2ResultsDirectoryFormat
)

# Register CheckM2 transformers
plugin.register_transformer(
    _checkm2_results_format_to_dataframe,
    inputs=(CheckM2ResultsFormat,),
    outputs=(pd.DataFrame,)
)
plugin.register_transformer(
    _dataframe_to_checkm2_results_format,
    inputs=(pd.DataFrame,),
    outputs=(CheckM2ResultsFormat,)
)
plugin.register_transformer(
    _checkm2_results_directory_to_dataframe,
    inputs=(CheckM2ResultsDirectoryFormat,),
    outputs=(pd.DataFrame,)
)
plugin.register_transformer(
    _checkm2_results_to_metadata,
    inputs=(CheckM2ResultsDirectoryFormat,),
    outputs=(qiime2.Metadata,)
)

# CheckM2 parameters
checkm2_params = {
    "database_path": Str,
    "threads": Int % Range(1, None),
    "force_model": Str,
    "lowmem": Bool,
    "genes": Bool,
    "extension": Str,
}

checkm2_param_descriptions = {
    "database_path": "Path to the CheckM2 database. If not provided, uses the "
                     "default database location or CHECKM2DB environment variable.",
    "threads": "Number of threads to use for processing. Default: 1.",
    "force_model": "Force the use of a specific completeness model ('specific' "
                   "or 'general'). If not provided, CheckM2 will automatically "
                   "select the appropriate model.",
    "lowmem": "Use low memory mode to reduce DIAMOND RAM usage by half at the "
              "expense of longer runtime.",
    "genes": "Indicates if the input files contain predicted protein sequences "
             "(genes) rather than nucleotide sequences.",
    "extension": "File extension of the input files. Default: 'fasta'.",
}

# Register CheckM2 action
plugin.methods.register_function(
    function=quality_control,
    inputs={
        "bins": SampleData[MAGs],
    },
    parameters=checkm2_params,
    outputs=[
        ("quality_report", CheckM2Results),
    ],
    input_descriptions={
        "bins": "MAGs to be analyzed for quality assessment.",
    },
    parameter_descriptions=checkm2_param_descriptions,
    output_descriptions={
        "quality_report": "CheckM2 quality assessment results containing "
                          "completeness and contamination estimates.",
    },
    name="Assess genome quality using CheckM2",
    description="This method uses CheckM2 to predict the completeness and "
                "contamination of metagenome-assembled genomes (MAGs) using "
                "machine learning models.",
    citations=[
        citations["parks2015b"],  # CheckM citation as foundation
    ],
)

# Register original CheckM visualizer
plugin.visualizers.register_function(
    function=q2_checkm.evaluate_bins,
    inputs={
        "bins": SampleData[MAGs],
    },
    parameters=checkm_params,
    input_descriptions={
        "bins": "MAGs to be analyzed.",
    },
    parameter_descriptions=checkm_param_descriptions,
    name="Evaluate quality of the generated MAGs using CheckM.",
    description="This method uses CheckM to assess the quality of assembled MAGs.",
    citations=[
        citations["matsen2010"],
        citations["hyatt2012"],
        citations["parks2015b"],
        citations["hmmer2022"],
    ],
)
