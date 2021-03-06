#!/usr/bin/env python


"""
maf_intersect.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This script takes two input MAF files and outputs the mutations
common to both, based on chromosome, position and alternate allele.

Example Use
~~~~~~~~~~~
python integrate_exome_and_genome.py -i input1.maf input2.maf \
    -o intersect.maf
"""


import argparse


MAF_FIELDNAMES = [
    'Hugo_Symbol', 'Entrez_Gene_Id', 'Center', 'NCBI_Build',
    'Chromosome', 'Start_Position', 'End_Position', 'Strand',
    'Variant_Classification', 'Variant_Type', 'Reference_Allele',
    'Tumor_Seq_Allele1', 'Tumor_Seq_Allele2', 'dbSNP_RS',
    'dbSNP_Val_Status', 'Tumor_Sample_Barcode',
    'Matched_Norm_Sample_Barcode', 'Match_Norm_Seq_Allele1',
    'Match_Norm_Seq_Allele2', 'Tumor_Validation_Allele1',
    'Tumor_Validation_Allele2', 'Match_Norm_Validation_Allele1',
    'Match_Norm_Validation_Allele2', 'Verification_Status',
    'Validation_Status', 'Mutation_Status', 'Sequencing_Phase',
    'Sequence_Source', 'Validation_Method', 'Score', 'BAM_File',
    'Sequencer', 'Tumor_Sample_UUID', 'Matched_Norm_Sample_UUID',
    'Annotation_Transcript', 'Transcript_Position', 'cDNA_Change',
    'Protein_Change', 'effect', 'categ']


def main():
    """Run maf_intersect.py
    """
    # Specify command line arguments
    parser = argparse.ArgumentParser(description='Obtain the intersect ' +
                                     'between two MAF files.')
    parser.add_argument('-i', '--input', nargs=2, type=argparse.FileType('r'),
                        required=True,
                        help='Specify the two MAF files whose intersect ' +
                        'you\'re interested in.')
    parser.add_argument('-o', '--output', nargs=1, type=argparse.FileType('w'),
                        required=True,
                        help='Specify where you want the MAF rows present ' +
                        'in both input MAF files to be outputted.')
    parser.add_argument('-m', '--merge', action='store_true', default=False,
                        help='Instead of finding the intersecting MAF rows, ' +
                        'this script merges both MAF files such that there ' +
                        'are no duplicate rows.')

    # Parse command line arguments
    args = parser.parse_args()
    input_maf_1 = args.input[0]
    input_maf_2 = args.input[1]
    output_maf = args.output[0]
    is_merging = args.merge

    # Obtain MAF rows and sort them
    maf_rows_1 = maf_row_generator(sorted(map(parse_maf_row,
                                   input_maf_1.readlines()),
                                   cmp=compare_maf_rows))
    maf_rows_2 = maf_row_generator(sorted(map(parse_maf_row,
                                   input_maf_2.readlines()),
                                   cmp=compare_maf_rows))

    # Compare the two input MAF files
    row_dict_1 = next(maf_rows_1, None)
    row_dict_2 = next(maf_rows_2, None)
    while row_dict_1 is not None and row_dict_2 is not None:
        if row_dict_1['Chromosome'] == row_dict_2['Chromosome']:
            if (int(row_dict_1['Start_Position']) ==
                    int(row_dict_2['Start_Position'])):
                if (row_dict_1['Tumor_Seq_Allele1'] ==
                        row_dict_2['Tumor_Seq_Allele1']):
                    output_maf.write(recreate_maf_row(row_dict_1))
                    row_dict_1 = next(maf_rows_1, None)
                    row_dict_2 = next(maf_rows_2, None)
                else:  # Alternate allele don't match
                    if (row_dict_1['Tumor_Seq_Allele1'] >
                            row_dict_2['Tumor_Seq_Allele1']):
                        if is_merging:
                            output_maf.write(recreate_maf_row(row_dict_2))
                        row_dict_2 = next(maf_rows_2, None)
                    else:   # row_dict_1['Tumor_Seq_Allele1'] <
                            # row_dict_2['Tumor_Seq_Allele1']
                        if is_merging:
                            output_maf.write(recreate_maf_row(row_dict_2))
                        row_dict_1 = next(maf_rows_1, None)
            else:  # If positions don't match
                if (int(row_dict_1['Start_Position']) >
                        int(row_dict_2['Start_Position'])):
                    if is_merging:
                        output_maf.write(recreate_maf_row(row_dict_2))
                    row_dict_2 = next(maf_rows_2, None)
                else:  # row_dict_1['Start_Position'] <
                       # row_dict_2['Start_Position']:
                    if is_merging:
                        output_maf.write(recreate_maf_row(row_dict_1))
                    row_dict_1 = next(maf_rows_1, None)
        else:  # If the chromosome don't match
            if row_dict_1['Chromosome'] > row_dict_2['Chromosome']:
                if is_merging:
                    output_maf.write(recreate_maf_row(row_dict_2))
                row_dict_2 = next(maf_rows_2, None)
            else:  # row_dict_1['Chromosome'] < row_dict_2['Chromosome']
                if is_merging:
                    output_maf.write(recreate_maf_row(row_dict_1))
                row_dict_1 = next(maf_rows_1, None)

    # If merging, continue until the end of the files
    if is_merging:
        if row_dict_1 is None and row_dict_2 is None:
            # Okay, we're done
            pass
        elif row_dict_1 is None and row_dict_2 is not None:
            # We need to finish maf_rows_2
            for leftover_row in maf_rows_2:
                output_maf.write(recreate_maf_row(leftover_row))
        elif row_dict_1 is not None and row_dict_2 is None:
            # We need to finish maf_rows_1
            for leftover_row in maf_rows_1:
                output_maf.write(recreate_maf_row(leftover_row))

    # Close the files
    input_maf_1.close()
    input_maf_2.close()
    output_maf.close()


def parse_maf_row(row):
    """Parse MAF row by creating a dictionary, with a key-value
    pair for each column, according to MAF_FIELDNAMES.
    """
    row_items = row.rstrip('\n').split('\t')
    row_dict = dict(zip(MAF_FIELDNAMES, row_items))
    row_dict['row'] = row
    return row_dict


def compare_maf_rows(row_dict_1, row_dict_2):
    """Compare two parsed MAF rows for sorting.
    """
    if row_dict_1['Chromosome'] > row_dict_2['Chromosome']:
        return 1
    elif row_dict_1['Chromosome'] < row_dict_2['Chromosome']:
        return -1
    else:  # Same chromosome
        if (int(row_dict_1['Start_Position']) >
                int(row_dict_2['Start_Position'])):
            return 1
        elif (int(row_dict_1['Start_Position']) <
              int(row_dict_2['Start_Position'])):
            return -1
        else:  # Same position
            if (row_dict_1['Tumor_Seq_Allele1'] >
                    row_dict_2['Tumor_Seq_Allele1']):
                return 1
            elif (row_dict_1['Tumor_Seq_Allele1'] >
                    row_dict_2['Tumor_Seq_Allele1']):
                return -1
            else:  # Same position
                return 0
    # This point shouldn't be reached
    raise Exception('Cannot sort MAF file.')


def maf_row_generator(maf_rows):
    """Create generator from list of parsed MAF rows.
    """
    for row in maf_rows:
        if row['Hugo_Symbol'] == 'Hugo_Symbol':
            continue
        yield row


def recreate_maf_row(row_dict):
    """Recreate a MAF row from a parsed MAF row (dictionary).
    """
    # recreated_row = ''
    # for column in MAF_FIELDNAMES:
    #     recreated_row += row_dict[column] + '\t'
    # recreated_row += '\n'
    recreated_row = row_dict['row']
    return recreated_row


if __name__ == '__main__':
    main()
