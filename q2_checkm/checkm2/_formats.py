# ----------------------------------------------------------------------------
# Copyright (c) 2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd
from qiime2.plugin import ValidationError, model


class CheckM2ResultsFormat(model.TextFileFormat):
    """
    Format for CheckM2 quality assessment results.
    
    This format represents a TSV file with CheckM2 genome quality results
    containing columns such as Name, Completeness, Contamination, etc.
    """
    
    def _validate_(self, level):
        try:
            df = pd.read_csv(str(self), sep='\t')
        except Exception as e:
            raise ValidationError(f"Failed to parse CheckM2 results file: {e}")
        
        # Check required columns
        required_columns = ['Name', 'Completeness', 'Contamination']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValidationError(
                f"Missing required columns in CheckM2 results: {missing_columns}"
            )
        
        # Validate data types and ranges
        if not df['Completeness'].dtype.kind in 'iufc':
            raise ValidationError("Completeness column must contain numeric values")
        if not df['Contamination'].dtype.kind in 'iufc':
            raise ValidationError("Contamination column must contain numeric values")
        
        # Check value ranges (allow some flexibility for edge cases)
        if (df['Completeness'] < 0).any() or (df['Completeness'] > 150).any():
            raise ValidationError(
                "Completeness values must be between 0 and 150 (percent)"
            )
        if (df['Contamination'] < 0).any():
            raise ValidationError(
                "Contamination values must be non-negative"
            )


class CheckM2ResultsDirectoryFormat(model.DirectoryFormat):
    """
    Directory format for CheckM2 results.
    
    Expected structure:
    quality_report.tsv  # Main results file
    """
    
    quality_report = model.File('quality_report.tsv', format=CheckM2ResultsFormat) 