""" Adjust csv layout """
import os
import csv
import yaml

# Set the maximum field size to 2MB to avoid the error "field larger than field limit (131072)"
OVER_SIZE_LIMIT = 2_000_000
csv.field_size_limit(OVER_SIZE_LIMIT)


class CsvConverter:
    """Class to adjust the layout and encoding of the CSV file extracted from QAWeb"""

    @classmethod
    def load_column_map(cls, map_file):
        """load columnm map config file"""
        with open(map_file, 'r', encoding='utf-8_sig') as file:
            return yaml.safe_load(file)['column_map']

    @classmethod
    def convert_csv(cls, input_file, output_file, map_file):
        """convert csv data"""

        # Check if the output file already exists
        if os.path.exists(output_file):
            raise ValueError("Output file already exists. file name: " + output_file)

        column_map = cls.load_column_map(map_file)

        with open(input_file, 'r', encoding='cp932', errors='replace') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)

        with open(output_file, 'w', encoding='utf-8_sig', newline='', errors='replace') as outfile:
            fieldnames = [col['name'] for col in column_map]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                new_row = {}
                for col in column_map:
                    if col['type'] == 'map':
                        new_row[col['name']] = row[col['source']]
                    elif col['type'] == 'const':
                        new_row[col['name']] = col['value']
                    elif col['type'] == 'blank':
                        new_row[col['name']] = ''
                writer.writerow(new_row)
