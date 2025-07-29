# ----------------------------------------------------------------------------
# Copyright (c) 2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import tempfile
from typing import Optional

from q2_types.per_sample_sequences import MultiMAGSequencesDirFmt

from q2_checkm.utils import run_command
from ._formats import CheckM2ResultsDirectoryFormat


def quality_control(
    bins: MultiMAGSequencesDirFmt,
    database_path: Optional[str] = None,
    threads: int = 1,
    force_model: Optional[str] = None,
    lowmem: bool = False,
    genes: bool = False,
    extension: str = "fasta"
) -> CheckM2ResultsDirectoryFormat:
    """
    Assess genome quality of MAGs using CheckM2.
    
    This method uses CheckM2 to predict the completeness and contamination
    of metagenome-assembled genomes (MAGs) using machine learning models.
    
    Parameters
    ----------
    bins : MultiMAGSequencesDirFmt
        MAGs to be analyzed.
    database_path : str, optional
        Path to the CheckM2 database. If not provided, uses the default
        database location or CHECKM2DB environment variable.
    threads : int, default 1
        Number of threads to use for processing.
    force_model : str, optional
        Force the use of a specific completeness model ('specific' or 'general').
        If not provided, CheckM2 will automatically select the appropriate model.
    lowmem : bool, default False
        Use low memory mode to reduce DIAMOND RAM usage by half at the expense
        of longer runtime.
    genes : bool, default False
        Indicates if the input files contain predicted protein sequences 
        (genes) rather than nucleotide sequences.
    extension : str, default "fasta"
        File extension of the input files.
        
    Returns
    -------
    CheckM2ResultsDirectoryFormat
        Quality assessment results containing completeness and contamination
        estimates for each input genome.
    """
    results = CheckM2ResultsDirectoryFormat()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Prepare the CheckM2 command
        cmd = ["checkm2", "predict"]
        cmd.extend(["--threads", str(threads)])
        cmd.extend(["--input", str(bins)])
        cmd.extend(["--output-directory", tmp_dir])
        cmd.extend(["--extension", extension])
        
        # Add optional parameters
        if database_path:
            cmd.extend(["--database_path", database_path])
        
        if force_model:
            if force_model not in ['specific', 'general']:
                raise ValueError("force_model must be 'specific' or 'general'")
            cmd.extend(["--force", force_model])
        
        if lowmem:
            cmd.append("--lowmem")
            
        if genes:
            cmd.append("--genes")
        
        # Set environment variables if database_path is provided
        env = os.environ.copy()
        if database_path:
            env["CHECKM2DB"] = database_path
        
        # Run CheckM2
        run_command(cmd, env=env)
        
        # Copy the results to the output directory
        quality_report_path = os.path.join(tmp_dir, "quality_report.tsv")
        if not os.path.exists(quality_report_path):
            raise FileNotFoundError(
                f"CheckM2 quality report not found at {quality_report_path}"
            )
        
        # Copy the quality report to the results directory
        import shutil
        shutil.copy2(quality_report_path, str(results.quality_report))
    
    return results 