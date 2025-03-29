'''Test CsvConverter'''
import tempfile
import os
import pytest
from app.scripts.modules.csv_converter import CsvConverter

class TestCsvConverter:
    '''Test CsvConverter'''

    def setup_method(self):
        self.input_csv_content = """source_col1,source_col2,source_col3
value11,value12,value13
value21,value22,value23
"""
        self.column_map_content = """
column_map:
  - name: "out_col1"
    type: "map"
    source: "source_col1"
    
  - name: "out_col2"
    type: "const"
    value: "constant_value"
  - name: "out_col3"
    type: "blank"
"""
        self.expected_output_csv_content = """out_col1,out_col2,out_col3
value11,constant_value,
value21,constant_value,
"""

    def test_convert_csv_success(self):
        '''Test CsvConverter'''
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='cp932') as input_file:
            input_file.write(self.input_csv_content)
            input_file_name = input_file.name

        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8_sig') as map_file:
            map_file.write(self.column_map_content)
            map_file_name = map_file.name

        output_file_name = tempfile.mktemp()

        try:
            CsvConverter.convert_csv(input_file_name, output_file_name, map_file_name)

            with open(output_file_name, 'r', encoding='utf-8_sig') as output_file:
                output_content = output_file.read()

            assert output_content == self.expected_output_csv_content
        finally:
            os.remove(input_file_name)
            os.remove(map_file_name)
            os.remove(output_file_name)

    def test_convert_csv_failure_output_file_exists(self):
        '''Test CsvConverter with existing output file'''
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='cp932') as input_file:
            input_file.write(self.input_csv_content)
            input_file_name = input_file.name

        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8_sig') as map_file:
            map_file.write(self.column_map_content)
            map_file_name = map_file.name

        output_file_name = tempfile.mktemp()

        try:
            with open(output_file_name, 'w', encoding='utf-8_sig') as output_file:
                output_file.write("dummy content")

            with pytest.raises(ValueError, match="Output file already exists. file name: " + output_file_name):
                CsvConverter.convert_csv(input_file_name, output_file_name, map_file_name)
        finally:
            os.remove(input_file_name)
            os.remove(map_file_name)
            os.remove(output_file_name)
