# ----------------------------------------------------------------------------
# Copyright (c) 2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import contextlib
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, call

import pandas as pd
import qiime2
from pandas._testing import assert_frame_equal
from q2_types.per_sample_sequences import MultiMAGSequencesDirFmt
from qiime2.plugin.testing import TestPluginBase

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


class TestCheckM2(TestPluginBase):
    package = "q2_checkm.tests"

    def setUp(self):
        super().setUp()
        with contextlib.ExitStack() as stack:
            self._tmp = stack.enter_context(tempfile.TemporaryDirectory())
            self.addCleanup(stack.pop_all().close)
        
        # Set up test data
        self.bins = MultiMAGSequencesDirFmt(self.get_data_path("bins"), "r")
        self.database_path = "/fake/checkm2/database"

    def test_checkm2_results_format_validation_valid(self):
        """Test CheckM2ResultsFormat validation with valid data."""
        format_obj = CheckM2ResultsFormat(
            self.get_data_path("checkm2_quality_simple.tsv"), mode="r"
        )
        # Should not raise any exception
        format_obj.validate()

    def test_checkm2_results_format_validation_missing_columns(self):
        """Test CheckM2ResultsFormat validation with missing required columns."""
        # Create a temporary file with missing columns
        invalid_file = os.path.join(self._tmp, "invalid.tsv")
        with open(invalid_file, "w") as f:
            f.write("Name\tSomeOtherColumn\n")
            f.write("bin1\t123\n")
        
        format_obj = CheckM2ResultsFormat(invalid_file, mode="r")
        with self.assertRaisesRegex(qiime2.plugin.ValidationError, 
                                   "Missing required columns"):
            format_obj.validate()

    def test_checkm2_results_format_validation_invalid_completeness(self):
        """Test CheckM2ResultsFormat validation with invalid completeness values."""
        invalid_file = os.path.join(self._tmp, "invalid_completeness.tsv")
        with open(invalid_file, "w") as f:
            f.write("Name\tCompleteness\tContamination\n")
            f.write("bin1\t-5.0\t1.0\n")  # Invalid negative completeness
        
        format_obj = CheckM2ResultsFormat(invalid_file, mode="r")
        with self.assertRaisesRegex(qiime2.plugin.ValidationError,
                                   "Completeness values must be between 0 and 150"):
            format_obj.validate()

    def test_checkm2_results_format_validation_invalid_contamination(self):
        """Test CheckM2ResultsFormat validation with invalid contamination values."""
        invalid_file = os.path.join(self._tmp, "invalid_contamination.tsv")
        with open(invalid_file, "w") as f:
            f.write("Name\tCompleteness\tContamination\n")
            f.write("bin1\t95.0\t-2.0\n")  # Invalid negative contamination
        
        format_obj = CheckM2ResultsFormat(invalid_file, mode="r")
        with self.assertRaisesRegex(qiime2.plugin.ValidationError,
                                   "Contamination values must be non-negative"):
            format_obj.validate()

    def test_checkm2_results_directory_format(self):
        """Test CheckM2ResultsDirectoryFormat."""
        # Create a directory format instance
        dir_format = CheckM2ResultsDirectoryFormat()
        
        # Copy test data to the directory
        shutil.copy2(
            self.get_data_path("checkm2_quality_simple.tsv"),
            str(dir_format.quality_report)
        )
        
        # Validate the directory format
        dir_format.validate()
        
        # Check that the quality report can be accessed
        quality_report = dir_format.quality_report.view(CheckM2ResultsFormat)
        self.assertIsInstance(quality_report, CheckM2ResultsFormat)

    def test_checkm2_results_format_to_dataframe(self):
        """Test conversion from CheckM2ResultsFormat to DataFrame."""
        format_obj = CheckM2ResultsFormat(
            self.get_data_path("checkm2_quality_simple.tsv"), mode="r"
        )
        
        df = _checkm2_results_format_to_dataframe(format_obj)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn("Completeness", df.columns)
        self.assertIn("Contamination", df.columns)
        
        # Check specific values
        self.assertAlmostEqual(df.loc["test_bin_1", "Completeness"], 98.5)
        self.assertAlmostEqual(df.loc["test_bin_2", "Contamination"], 3.7)

    def test_dataframe_to_checkm2_results_format(self):
        """Test conversion from DataFrame to CheckM2ResultsFormat."""
        # Create test DataFrame
        data = {
            "Completeness": [95.0, 87.5, 92.3],
            "Contamination": [2.1, 4.8, 1.9]
        }
        df = pd.DataFrame(data, index=["bin1", "bin2", "bin3"])
        df.index.name = "Name"
        
        format_obj = _dataframe_to_checkm2_results_format(df)
        
        self.assertIsInstance(format_obj, CheckM2ResultsFormat)
        format_obj.validate()
        
        # Read back and verify
        df_read = _checkm2_results_format_to_dataframe(format_obj)
        assert_frame_equal(df, df_read)

    def test_checkm2_results_directory_to_dataframe(self):
        """Test conversion from CheckM2ResultsDirectoryFormat to DataFrame."""
        dir_format = CheckM2ResultsDirectoryFormat()
        shutil.copy2(
            self.get_data_path("checkm2_quality_simple.tsv"),
            str(dir_format.quality_report)
        )
        
        df = _checkm2_results_directory_to_dataframe(dir_format)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn("Completeness", df.columns)
        self.assertIn("Contamination", df.columns)

    def test_checkm2_results_to_metadata(self):
        """Test conversion from CheckM2Results to qiime2.Metadata."""
        dir_format = CheckM2ResultsDirectoryFormat()
        shutil.copy2(
            self.get_data_path("checkm2_quality_simple.tsv"),
            str(dir_format.quality_report)
        )
        
        metadata = _checkm2_results_to_metadata(dir_format)
        
        self.assertIsInstance(metadata, qiime2.Metadata)
        df = metadata.to_dataframe()
        self.assertEqual(len(df), 3)
        self.assertIn("Completeness", df.columns)
        self.assertIn("Contamination", df.columns)

    @patch("subprocess.run")
    def test_quality_control_basic(self, mock_run):
        """Test basic quality_control function."""
        # Create a mock CheckM2 output directory
        mock_output_dir = os.path.join(self._tmp, "checkm2_output")
        os.makedirs(mock_output_dir)
        
        # Create a mock quality report
        quality_report_path = os.path.join(mock_output_dir, "quality_report.tsv")
        shutil.copy2(
            self.get_data_path("checkm2_quality_simple.tsv"),
            quality_report_path
        )
        
        # Mock the run_command function to avoid actual CheckM2 execution
        with patch("q2_checkm.checkm2._methods.run_command") as mock_run_cmd:
            # Mock tempfile.TemporaryDirectory to return our mock directory
            with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
                mock_tmpdir.return_value.__enter__.return_value = mock_output_dir
                
                result = quality_control(
                    bins=self.bins,
                    threads=2,
                    database_path=self.database_path
                )
        
        # Verify the result
        self.assertIsInstance(result, CheckM2ResultsDirectoryFormat)
        
        # Verify the command was called correctly
        mock_run_cmd.assert_called_once()
        args, kwargs = mock_run_cmd.call_args
        cmd = args[0]
        
        self.assertIn("checkm2", cmd)
        self.assertIn("predict", cmd)
        self.assertIn("--threads", cmd)
        self.assertIn("2", cmd)
        self.assertIn("--database_path", cmd)
        self.assertIn(self.database_path, cmd)

    @patch("subprocess.run")
    def test_quality_control_with_options(self, mock_run):
        """Test quality_control function with various options."""
        mock_output_dir = os.path.join(self._tmp, "checkm2_output")
        os.makedirs(mock_output_dir)
        
        quality_report_path = os.path.join(mock_output_dir, "quality_report.tsv")
        shutil.copy2(
            self.get_data_path("checkm2_quality_simple.tsv"),
            quality_report_path
        )
        
        with patch("q2_checkm.checkm2._methods.run_command") as mock_run_cmd:
            with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
                mock_tmpdir.return_value.__enter__.return_value = mock_output_dir
                
                result = quality_control(
                    bins=self.bins,
                    threads=4,
                    force_model="specific",
                    lowmem=True,
                    genes=True,
                    extension="fna"
                )
        
        # Verify the command was called with correct parameters
        mock_run_cmd.assert_called_once()
        args, kwargs = mock_run_cmd.call_args
        cmd = args[0]
        
        self.assertIn("--threads", cmd)
        self.assertIn("4", cmd)
        self.assertIn("--force", cmd)
        self.assertIn("specific", cmd)
        self.assertIn("--lowmem", cmd)
        self.assertIn("--genes", cmd)
        self.assertIn("--extension", cmd)
        self.assertIn("fna", cmd)

    def test_quality_control_invalid_force_model(self):
        """Test quality_control with invalid force_model parameter."""
        with self.assertRaises(ValueError) as cm:
            quality_control(
                bins=self.bins,
                force_model="invalid_model"
            )
        
        self.assertIn("force_model must be 'specific' or 'general'", str(cm.exception))

    @patch("subprocess.run")
    def test_quality_control_missing_output(self, mock_run):
        """Test quality_control when CheckM2 doesn't produce output."""
        mock_output_dir = os.path.join(self._tmp, "checkm2_output")
        os.makedirs(mock_output_dir)
        # Note: NOT creating the quality_report.tsv file
        
        with patch("q2_checkm.checkm2._methods.run_command") as mock_run_cmd:
            with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
                mock_tmpdir.return_value.__enter__.return_value = mock_output_dir
                
                with self.assertRaises(FileNotFoundError) as cm:
                    quality_control(bins=self.bins)
        
        self.assertIn("CheckM2 quality report not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main() 