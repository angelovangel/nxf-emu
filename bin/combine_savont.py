#!/usr/bin/env python3
import sys
import os
import csv

def main():
    if len(sys.argv) < 3:
        print("Usage: combine_savont.py <output_file> <input_files...>")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    tax_cols = ['tax_id', 'species', 'genus', 'family', 'order', 'class', 'phylum', 'clade', 'superkingdom']
    combined_data = {} # (tax_tuple) -> {sample: abundance}
    samples = []

    for f in input_files:
        sample_name = os.path.basename(f).replace('_rel-abundance.tsv', '')
        samples.append(sample_name)
        
        with open(f, 'r') as tsv_file:
            reader = csv.DictReader(tsv_file, delimiter='\t')
            if not reader.fieldnames:
                continue
            for row in reader:
                # Create a key from taxonomy
                tax_key = tuple(row.get(col, 'Unknown') for col in tax_cols)
                if tax_key not in combined_data:
                    combined_data[tax_key] = {}
                combined_data[tax_key][sample_name] = row.get('abundance', '0')

    # Sort samples for consistency
    samples.sort()

    with open(output_file, 'w', newline='') as out_file:
        writer = csv.writer(out_file, delimiter='\t')
        # Header
        writer.writerow(tax_cols + samples)
        
        # Rows
        for tax_key, sample_values in combined_data.items():
            row = list(tax_key)
            for s in samples:
                row.append(sample_values.get(s, '0'))
            writer.writerow(row)

if __name__ == "__main__":
    main()
