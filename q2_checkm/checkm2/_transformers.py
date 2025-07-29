# ----------------------------------------------------------------------------
# Copyright (c) 2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd
import qiime2

from ._formats import CheckM2ResultsFormat, CheckM2ResultsDirectoryFormat
from ._types import CheckM2Results


def _checkm2_results_format_to_dataframe(ff: CheckM2ResultsFormat) -> pd.DataFrame:
    """Convert CheckM2ResultsFormat to pandas DataFrame."""
    df = pd.read_csv(str(ff), sep='\t', index_col=0)
    return df


def _dataframe_to_checkm2_results_format(df: pd.DataFrame) -> CheckM2ResultsFormat:
    """Convert pandas DataFrame to CheckM2ResultsFormat."""
    ff = CheckM2ResultsFormat()
    df.to_csv(str(ff), sep='\t', index=True)
    return ff


def _checkm2_results_directory_to_dataframe(
    dirfmt: CheckM2ResultsDirectoryFormat
) -> pd.DataFrame:
    """Convert CheckM2ResultsDirectoryFormat to pandas DataFrame."""
    return _checkm2_results_format_to_dataframe(dirfmt.quality_report.view(CheckM2ResultsFormat))


def _checkm2_results_to_metadata(
    dirfmt: CheckM2ResultsDirectoryFormat
) -> qiime2.Metadata:
    """Convert CheckM2Results to qiime2.Metadata."""
    df = _checkm2_results_directory_to_dataframe(dirfmt)
    
    # Ensure the index has a name for metadata
    if df.index.name is None:
        df.index.name = 'sample-id'
    
    return qiime2.Metadata(df) 