# epidemiological-overlap
Scripts to contextualize Enterobacterales isolate transmission linkages with patient metadata and related analyses.

Based on work to recreate analyses in [Whole genome sequencing reveals hidden transmission of carbapenemase-producing Enterobacterales](https://doi.org/10.1038/s41467-022-30637-5) and [Plasmid dynamics driving carbapenemase gene dissemination in healthcare environments: a nationwide analysis of closed Enterobacterales genomes](https://doi.org/10.1038/s41467-025-64515-7).

Other sources of reference:
https://github.com/nataschamay/cp_transmission_2021

## Overview

This repository contains a small analysis workflow for comparing isolate pairs against patient metadata and generating epidemiological overlap outputs.

The main workflow script is [tools/Address_epiOverlap.py](tools/Address_epiOverlap.py). It reads a set of TSV inputs, resolves isolate-to-patient mappings, compares patient addresses, and writes output files summarising overlap events and per-pair status.

## Environment setup

Create and activate a virtual environment, then install the project dependencies:

```bash
cd /path/to/epidemiological-overlap
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Finding address overlap

### Check the CLI usage

```bash
python ./tools/Address_epiOverlap.py --help
```

This shows the required arguments and the expected input schema.

### Run the analysis

```bash
python ./tools/Address_epiOverlap.py \
  --isolate_DOC ./data/demo/inputs/Isolate_DOC_decimal.tsv \
  --isolate_patient_mapping ./data/demo/inputs/Isolate-patient_ID_mapping.tsv \
  --patient_address ./data/demo/inputs/Patient_addresses.tsv \
  --isolate_pairs ./data/demo/inputs/Recipient-donor_isolate_pairs.tsv \
  --output_folder ./data/testout
```

This writes files such as:

- `Address_epiOverlap_events.tsv`
- `Address_epiOverlap_statuses_all_pairs.tsv`
- `Address_epiOverlap_Argslog.txt`

into the output folder you specify.

### Input and output files

The script reads TSV files by column position, not by exact header names. For the default schema and detailed file descriptions, see:

- [Isolate_DOC_decimal.tsv](data/README.md#isolate_doc_decimaltsv)
- [Isolate-patient_ID_mapping.tsv](data/README.md#isolate-patient_id_mappingtsv)
- [Patient_addresses.tsv](data/README.md#patient_addressestsv)
- [Recipient-donor_isolate_pairs.tsv](data/README.md#recipient-donor_isolate_pairstsv)
- [Address_epiOverlap_events.tsv](data/README.md#address_epioverlap_eventstsv)
- [Address_epiOverlap_statuses_all_pairs.tsv](data/README.md#address_epioverlap_statuses_all_pairstsv)

## Custom column order

If a file has a different layout, you can override the expected column positions directly in the path. All scripts use the numbered order you provide rather than matching on explicit column names.

Example:

```bash
python ./tools/Address_epiOverlap.py \
  --patient_address ./data/my_inputs/addresses.tsv[1,3,2,5] \
  --isolate_DOC ./data/my_inputs/isolate_doc.tsv[2,1] \
  --isolate_patient_mapping ./data/my_inputs/mapping.tsv[2,1] \
  --isolate_pairs ./data/my_inputs/pairs.tsv[2,1] \
  --output_folder ./data/testout
```

In this example, the parser reads the specified numeric columns in the order shown before processing the file. This lets you keep the same script logic even when the input files use different column layouts or alternate header names.

## Notes

- Missing values such as `n.a` or blank cells are treated as absent where applicable.
- Date values can include standard ISO formats, slash-delimited dates, hyphen-delimited dates, and decimal-year values.
- The script is intended for TSV inputs and assumes a header row is present, but it does not rely on exact header names.
