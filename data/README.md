## Descriptions of input data

### Isolate_DOC_decimal.tsv
* Description:
    * A per-isolate culture-date file used to determine the date of culture for each isolate.
    * The project accepts ISO dates, decimal-year values, slash-delimited dates, and hyphen-delimited dates.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
* Analogous to the `list_dateOfCulture` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Isolate_ID`
    2. `Date of Culture (DOC)`
* Example rows:
    * `ISO201    2010-09-06`
    * `ISO202    2010.682192`
    * `ISO203    06/09/2010`

### Isolate-patient_ID_mapping.tsv
* Description:
    * A lookup table linking each isolate to the patient it belongs to.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
* Analogous to the `list_capesID` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Isolate_ID`
    2. `Patient_ID`
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
    1. `Patient_ID`
    2. `Postal code`
    3. `Unit number`
    4. `Row Number`
* Example rows:
    * `PID101    123456    05-07    6`
    * `PID102    654321    3-110    7`

### Patient_admission_details.tsv
* Description:
    * A patient-level admission table containing age, sex, admission/discharge dates, hospital, ward, bed, and discipline overlap metadata used by the discipline workflow.
* Input for:
    * tools/Discipline_epiOverlap.py
* Analogous to the `list_adm` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Patient_ID`
    2. `Age`
    3. `Gender`
    4. `Admission Date`
    5. `Discharge Date`
    6. `Admission Hospital`
    7. `Ward`
    8. `Bed`
    9. `Discipline`
    10. `Start Date`
    11. `Stop Date`
* Example rows:
    * `PID101    45    M    2020-01-01    2020-01-10    Hospital A    Ward 1    Bed 5    Cardiology    2020-01-01    2020-01-05`
    * `PID102    60    F    2020-02-01    2020-02-15    Hospital B    Ward 2    Bed 10    Neurology    2020-02-01    2020-02-10`

### Recipient-donor_isolate_pairs.tsv
* Description:
    * A table of recipient/donor isolate pairs to assess whether the corresponding patients share a similar address or overlap within the same hospital and discipline window.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
* Analogous to the `list_glbtpairs` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
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
    1. `Overlap_event_type`
    2. `Recip_patient_ID`
    3. `Donor_patient_ID`
    4. `Recip_patient_address_hash`
    5. `Donor_patient_address_hash`

### Address_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate recipient/donor combinations and whether each pair overlaps by postal code and/or unit number.
* Output yielded by:
    * tools/Address_epiOverlap.py
* Analogous to the `EpiOverlap_Address_status` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
    3. `Recip_patient_ID`
    4. `Donor_patient_ID`
    5. `Postal_code_overlap`
    6. `Unit_number_overlap`

### Discipline_epiOverlap_events.tsv
* Description:
    * Event-level record for each recipient-donor pair and stay combination where the same discipline and hospital overlap is observed.
    * The event type distinguishes exact, partial, indirect, and no-contact relationships.
* Output yielded by:
    * tools/Discipline_epiOverlap.py
* Output columns:
    1. `Overlap_event_type`
    2. `Recip_patient_ID`
    3. `Recip_isolate_ID`
    4. `Recip_isolate_DOC`
    5. `Recip_Age`
    6. `Recip_Gender`
    7. `Recip_Admission_date`
    8. `Recip_Discharge_Date`
    9. `Recip_Admission_Hospital`
    10. `Recip_Ward`
    11. `Recip_Bed`
    12. `Recip_Discipline`
    13. `Recip_start_date`
    14. `Recip_end_date`
    15. `Donor_patient_ID`
    16. `Donor_isolate_ID`
    17. `Donor_isolate_DOC`
    18. `Donor_Age`
    19. `Donor_Gender`
    20. `Donor_Admission_date`
    21. `Donor_Discharge_Date`
    22. `Donor_Admission_Hospital`
    23. `Donor_Ward`
    24. `Donor_Bed`
    25. `Donor_Discipline`
    26. `Donor_start_date`
    27. `Donor_end_date`

### Discipline_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate recipient/donor combinations and whether each pair overlaps by discipline within the same hospital.
* Output yielded by:
    * tools/Discipline_epiOverlap.py
* Analogous to the `EpiOverlap_Adm_DiscSum` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
    3. `Recip_patient_ID`
    4. `Donor_patient_ID`
    5. `Direct_exact_discipline_contact`
    6. `Direct_partial_discipline_contact`
    7. `Indirect_discipline_contact`
    8. `No_discipline_contact`
    9. `Date_OOR`

### Discipline_epiOverlap_Argslog.txt
* Description:
    * A copy of the CLI arguments used to generate the discipline output files.
* Output yielded by:
    * tools/Discipline_epiOverlap.py
* Notes:
    * This file records the input paths and the `--decimal_date` flag state for reproducibility.

