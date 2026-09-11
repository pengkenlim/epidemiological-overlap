## Descriptions of input data

### Isolate_DOC_decimal.tsv
* Description:
    * A per-isolate culture-date file used to determine the date of culture for each isolate.
    * The project accepts ISO dates, decimal-year values, slash-delimited dates, and hyphen-delimited dates.
* Input for:
    * tools/Address_epiOverlap.py
* Analogous to the `list_dateOfCulture` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    * `Isolate_ID`
    * `Date of Culture (DOC)`
* Example rows:
    * `ISO201    2010-09-06`
    * `ISO202    2010.682192`
    * `ISO203    06/09/2010`

### Isolate-patient_ID_mapping.tsv
* Description:
    * A lookup table linking each isolate to the patient it belongs to.
* Input for:
    * tools/Address_epiOverlap.py
* Analogous to the `list_capesID` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    * `Isolate_ID`
    * `Patient_ID`
* Example rows:
    * `ISO201    PID101`
    * `ISO202    PID102`

### Patient_addresses.tsv
* Description:
    * A patient-level address table containing postcode, unit number, and a row identifier.
    * The workflow compares postal code and unit number to determine whether pairs overlap at the address level.
* Input for:
    * tools/Address_epiOverlap.py
* Analogous to the `list_address` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    * `Patient_ID`
    * `Postal code`
    * `Unit number`
    * `Row Number`
* Example rows:
    * `PID101    123456    05-07    6`
    * `PID102    654321    3-110    7`

### Recipient-donor_isolate_pairs.tsv
* Description:
    * A table of recipient/donor isolate pairs to assess whether the corresponding patients share the same postcode or unit number.
* Input for:
    * tools/Address_epiOverlap.py
* Analogous to the `list_glbtpairs` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    * `Recip_isolate_ID`
    * `Donor_isolate_ID`
* Example rows:
    * `ISO201    ISO203`
    * `ISO202    ISO205`

## Descriptions of output data

### Address_epiOverlap_events.tsv
* Description:
    * Event-level record of the overlap type identified for each recipient-donor pair.
    * It can include events such as postcode overlap or unit-number overlap.
* Output yielded by:
    * tools/Address_epiOverlap.py
* Analogous to the `EpiOverlap_Address_full` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    * `Overlap_event_type`
    * `Recip_patient_ID`
    * `Donor_patient_ID`
    * `Recip_patient_address_hash`
    * `Donor_patient_address_hash`

### Address_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate recipient/donor combinations and whether each pair overlaps by postal code and/or unit number.
* Output yielded by:
    * tools/Address_epiOverlap.py
* Analogous to the `EpiOverlap_Address_status` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    * `Recip_isolate_ID`
    * `Donor_isolate_ID`
    * `Recip_patient_ID`
    * `Donor_patient_ID`
    * `Postal_code_overlap`
    * `Unit_number_overlap`
