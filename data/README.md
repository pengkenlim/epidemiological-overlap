## Descriptions of input data

### Isolate_DOC_decimal.tsv
* Description:
    * A per-isolate culture-date file used to determine the date of culture for each isolate.
    * The project accepts ISO dates, decimal-year values, slash-delimited dates, and hyphen-delimited dates.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
    * tools/Adm_epiOverlap.py
    * tools/Procedure_epiOverlap.py
* Analogous to the `list_dateOfCulture` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Isolate_ID`
    2. `Date of Culture (DOC)`
* Example rows:

| Isolate_ID | Date of Culture (DOC) |
| --- | --- |
| ISO201 | 2010-09-06 |
| ISO202 | 2010.682192 |
| ISO203 | 06/09/2010 |

### Isolate-patient_ID_mapping.tsv
* Description:
    * A lookup table linking each isolate to the patient it belongs to.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
    * tools/Adm_epiOverlap.py
    * tools/Procedure_epiOverlap.py
* Analogous to the `list_capesID` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Isolate_ID`
    2. `Patient_ID`
* Example rows:

| Isolate_ID | Patient_ID |
| --- | --- |
| ISO201 | PID101 |
| ISO202 | PID102 |

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

| Patient_ID | Postal code | Unit number | Row Number |
| --- | --- | --- | --- |
| PID101 | 123456 | 05-07 | 6 |
| PID102 | 654321 | 3-110 | 7 |

### Patient_admission_details.tsv
* Description:
    * A patient-level admission table containing age, sex, admission/discharge dates, hospital, ward, bed, and discipline metadata used by the discipline and admission workflows.
* Input for:
    * tools/Discipline_epiOverlap.py
    * tools/Adm_epiOverlap.py
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

| Patient_ID | Age | Gender | Admission Date | Discharge Date | Admission Hospital | Ward | Bed | Discipline | Start Date | Stop Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PID101 | 45 | M | 2020-01-01 | 2020-01-10 | Hospital A | Ward 1 | Bed 5 | Cardiology | 2020-01-01 | 2020-01-05 |
| PID102 | 60 | F | 2020-02-01 | 2020-02-15 | Hospital B | Ward 2 | Bed 10 | Neurology | 2020-02-01 | 2020-02-10 |

### Patient_hospital_procedures.tsv
* Description:
    * A patient-level procedure table with the patient identifier and hospital in the first two columns, followed by one column per procedure type.
    * The script expects the first two columns to always be patient ID and hospital, regardless of the header names used in the file.
    * Later columns are procedure-specific and their names must match the actual procedure names being evaluated, such as `OGD`, `Colonoscope`, and `ERCP`.
    * Each cell may contain one date or multiple dates separated by commas; each date is treated as a separate procedure occurrence for that procedure type.
* Input for:
    * tools/Procedure_epiOverlap.py
* Expected columns (by position):
    1. `Patient_ID`
    2. `Hospital`
    3. 3rd column onwards: One or more procedure columns, each named after a procedure type and containing date values for that procedure.
* Example rows:

| Patient_ID | Hospital | OGD | Colonoscopy | ERCP |
| --- | --- | --- | --- | --- |
| PID101 | Hospital A | 2010-09-06 | 2010-09-11,2010-09-12 | 2010-09-18 |
| PID102 | Hospital B |  | 2011-02-01 |  |

### Recipient-donor_isolate_pairs.tsv
* Description:
    * A table of recipient/donor isolate pairs used to assess whether the corresponding patients share a similar address or overlap within the same hospital or discipline window.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
    * tools/Adm_epiOverlap.py
    * tools/Procedure_epiOverlap.py
* Analogous to the `list_glbtpairs` input text file accepted by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Expected columns (by position):
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
* Example rows:

| Recip_isolate_ID | Donor_isolate_ID |
| --- | --- |
| ISO201 | ISO203 |
| ISO202 | ISO205 |

## Descriptions of output data

### Address_epiOverlap_events.tsv
* Description:
    * Event-level record between the recipient and donor of every isolate transmission-pair.
* Output yielded by:
    * tools/Address_epiOverlap.py
* Analogous to the `EpiOverlap_Address_full` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    1. `Overlap_event_type`
    * Possible values and their requirements:
        * `POSTCODE`
            * Indicates that the recipient and donor share the same postal code.
        * `UNIT_NUMBER`
            * Indicates that the recipient and donor share the same unit number and postal code.
    2. `Recip_patient_ID`
    3. `Donor_patient_ID`
    4. `Recip_patient_address_hash`
    5. `Donor_patient_address_hash`

### Address_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate transmission-pairs and their address overlap status within the same hospital.
* Output yielded by:
    * tools/Address_epiOverlap.py
* Analogous to the `EpiOverlap_Address_status` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
    3. `Recip_patient_ID`
    4. `Donor_patient_ID`
    5. `Postal_code_overlap`
        * `POSTCODE` if such an event has been established.
    6. `Unit_number_overlap`
        * `UNIT_NUMBER` if such an event has been established.

### Discipline_epiOverlap_events.tsv
* Description:
    * Event-level record for all possible valid hospital stay combinations between the recipient and donor of every isolate transmission-pair. Recipient and donor stays are considered valid for a given isolate transmission-pair if they fall within the risk period.
* Output yielded by:
    * tools/Discipline_epiOverlap.py
* Output columns:
    1. `Overlap_event_type`
    * Possible values and their requirements:
        * `Discipline Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same discipline and hospital.
        * `Discipline Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same discipline and hospital. This is mutually exclusive with `Discipline Direct (Exact)`.
        * `Discipline Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same discipline and hospital. The donor stay must precede that of the recipient.
        * `No Discipline Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same discipline and hospital, or the recipient stay entirely precedes that of the donor.
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
    * Pair-level summary of all isolate transmission-pairs and their discipline overlap status within the same hospital.
* Output yielded by:
    * tools/Discipline_epiOverlap.py
* Analogous to the `EpiOverlap_Adm_DiscSum` output text file yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
    3. `Recip_patient_ID`
    4. `Donor_patient_ID`
    5. `Direct_exact_discipline_contact`
        * `Discipline Direct (Exact)` if at least one such event is observed for the isolate transmission-pair.
    6. `Direct_partial_discipline_contact`
        * `Discipline Direct` if at least one such event is observed for the isolate transmission-pair.
    7. `Indirect_discipline_contact`
        * `Discipline Indirect` if at least one such event is observed for the isolate transmission-pair.
    8. `No_discipline_contact`
        * `Discipline No Contact` if at least one such event is observed for the isolate transmission-pair.
    9. `Date_OOR`
        * `Date_OOR` if at least one pair of recipient and donor stays is observed to be outside the risk-period overlap. This is mainly for troubleshooting and debugging. An isolate-transmission pair with ONLY this status only indicates that there are no valid stays within the risk period to determine contact.

### Adm_epiOverlap_events.tsv
* Description:
    * Event-level record for all possible valid hospital stay combinations between the recipient and donor of every isolate transmission-pair. Recipient and donor stays are considered valid for a given isolate transmission-pair if they fall within the risk period.
* Output yielded by:
    * tools/Adm_epiOverlap.py
* Output columns:
    1. `Hospital_Overlap_event_type`
    * Possible values and their requirements:
        * `Hospital Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same hospital.
        * `Hospital Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same hospital. This is mutually exclusive with `Hospital Direct (Exact)`.
        * `Hospital Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same hospital. The donor stay must precede that of the recipient.
        * `No Hospital Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same hospital, or the recipient stay entirely precedes that of the donor.
    2. `Ward_Overlap_event_type`
    * Possible values and their requirements:
        * `Ward Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same ward and hospital.
        * `Ward Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same ward and hospital. This is mutually exclusive with `Ward Direct (Exact)`.
        * `Ward Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same ward and hospital. The donor stay must precede that of the recipient.
        * `No Ward Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same ward and hospital, or the recipient stay entirely precedes that of the donor.
    3. `Bed_Overlap_event_type`
    * Possible values and their requirements:
        * `Bed Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same bed and hospital.
        * `Bed Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same bed and hospital. This is mutually exclusive with `Bed Direct (Exact)`.
        * `Bed Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same bed and hospital. The donor stay must precede that of the recipient.
        * `No Bed Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same bed and hospital, or the recipient stay entirely precedes that of the donor.
    4. `Recip_patient_ID`
    5. `Recip_isolate_ID`
    6. `Recip_isolate_DOC`
    7. `Recip_Age`
    8. `Recip_Gender`
    9. `Recip_Admission_date`
    10. `Recip_Discharge_Date`
    11. `Recip_Admission_Hospital`
    12. `Recip_Ward`
    13. `Recip_Bed`
    14. `Recip_Discipline`
    15. `Recip_start_date`
    16. `Recip_end_date`
    17. `Donor_patient_ID`
    18. `Donor_isolate_ID`
    19. `Donor_isolate_DOC`
    20. `Donor_Age`
    21. `Donor_Gender`
    22. `Donor_Admission_date`
    23. `Donor_Discharge_Date`
    24. `Donor_Admission_Hospital`
    25. `Donor_Ward`
    26. `Donor_Bed`
    27. `Donor_Discipline`
    28. `Donor_start_date`
    29. `Donor_end_date`

### Procedure_epiOverlap_events.tsv
* Description:
    * Event-level record for procedure comparisons between the recipient and donor of each isolate transmission-pair.
    * The comparison is performed only for donor and recipient procedures within the risk period corresponding to the isolate transmission-pair.
* Output yielded by:
    * tools/Procedure_epiOverlap.py
* Output columns:
    1. `Overlap_event_type`
        * `Procedure Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share the same procedure in the same hospital on the same day.
        * `Procedure Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share the same procedure in the same hospital, with the donor procedure date preceding the recipient procedure date.
        * `No Procedure Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share the same procedure in the same hospital, or they share the same procedure and hospital but the recipient procedure date precedes the donor procedure date.
    2. `Recip_patient_ID`
    3. `Recip_isolate_ID`
    4. `Recip_isolate_DOC`
    5. `Recip_procedure_hospital`
    6. `Recip_procedure`
    7. `Recip_procedure_date`
    8. `Donor_patient_ID`
    9. `Donor_isolate_ID`
    10. `Donor_isolate_DOC`
    11. `Donor_procedure_hospital`
    12. `Donor_procedure`
    13. `Donor_procedure_date`

### Procedure_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate transmission-pairs and whether they have direct procedure contact, indirect procedure contact, no procedure contact, date out-of-range, or no procedure data recorded.
* Output yielded by:
    * tools/Procedure_epiOverlap.py
* Output columns:
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
    3. `Recip_patient_ID`
    4. `Donor_patient_ID`
    5. `Direct_procedure_contact`
        * `Procedure Direct` if at least one such event is observed for the isolate transmission-pair.
    6. `Indirect_procedure_contact`
        * `Procedure Indirect` if at least one such event is observed for the isolate transmission-pair.
    7. `No_procedure_contact`
        * `No Procedure Contact` if at least one such event is observed for the isolate transmission-pair.
    8. `Date_OOR`
        * `Date_OOR` if at least one comparison of recipient and donor procedures has procedure dates outside the risk period. This is mainly for troubleshooting and debugging. An isolate-transmission pair with ONLY this status indicates that there are no valid procedures within the risk period to determine contact.
    9. `No_procedure`
        * `No Procedure for patient` if there are no procedure records available for at least one patient in the isolate transmission-pair.

### Adm_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate transmission-pairs and their hospital, ward, and bed overlap status within the same hospital.
* Output yielded by:
    * tools/Adm_epiOverlap.py
* Analogous to the combined information contained in the `EpiOverlap_Adm_HospSum`, `EpiOverlap_Adm_WardSum`, and `EpiOverlap_Adm_BedSum` output text files yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
* Output columns:
    1. `Recip_isolate_ID`
    2. `Donor_isolate_ID`
    3. `Recip_patient_ID`
    4. `Donor_patient_ID`
    5. `Direct_exact_hospital_contact`
        * `Hospital Direct (Exact)` if at least one such event is observed for the isolate transmission-pair.
    6. `Direct_partial_hospital_contact`
        * `Hospital Direct` if at least one such event is observed for the isolate transmission-pair.
    7. `Indirect_hospital_contact`
        * `Hospital Indirect` if at least one such event is observed for the isolate transmission-pair.
    8. `No_hospital_contact`
        * `No Hospital Contact` if at least one such event is observed for the isolate transmission-pair.
    9. `Direct_exact_ward_contact`
        * `Ward Direct (Exact)` if at least one such event is observed for the isolate transmission-pair.
    10. `Direct_partial_ward_contact`
        * `Ward Direct` if at least one such event is observed for the isolate transmission-pair.
    11. `Indirect_ward_contact`
        * `Ward Indirect` if at least one such event is observed for the isolate transmission-pair.
    12. `No_ward_contact`
        * `No Ward Contact` if at least one such event is observed for the isolate transmission-pair.
    13. `Indirect_bed_contact`
        * `Bed Indirect` if at least one such event is observed for the isolate transmission-pair.
    14. `No_bed_contact`
        * `No Bed Contact` if at least one such event is observed for the isolate transmission-pair.
    15. `Date_OOR`
        * `Date_OOR` if at least one pair of recipient and donor stays is observed to be out of risk period overlap. More for trouble shooting and debugging purposes. An isolate-transmission pair with ONLY this status  indicates that there are no valid stays within the risk period to determine contact.
