## Descriptions of input data

### Isolate_DOC_decimal.tsv
* Description:
    * A per-isolate culture-date file used to determine the date of culture for each isolate.
    * The project accepts ISO dates, decimal-year values, slash-delimited dates, and hyphen-delimited dates.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
    * tools/Adm_epiOverlap.py
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
    * tools/Adm_epiOverlap.py
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
    * `PID101    45    M    2020-01-01    2020-01-10    Hospital A    Ward 1    Bed 5    Cardiology    2020-01-01    2020-01-05`
    * `PID102    60    F    2020-02-01    2020-02-15    Hospital B    Ward 2    Bed 10    Neurology    2020-02-01    2020-02-10`

### Recipient-donor_isolate_pairs.tsv
* Description:
    * A table of recipient/donor isolate pairs to assess whether the corresponding patients share a similar address or overlap within the same hospital and discipline window.
* Input for:
    * tools/Address_epiOverlap.py
    * tools/Discipline_epiOverlap.py
    * tools/Adm_epiOverlap.py
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
            * Indicates that the recipient and donor share the same unit number AND postal code.
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
        * `POSTCODE` if such event has been established.
    6. `Unit_number_overlap`
        * `UNIT_NUMBER` if such event has been established.

### Discipline_epiOverlap_events.tsv
* Description:
    * Event-level record for all possible valid hospital stay combinations between the recipient and donor of every isolate transmission-pair. Recipient / donor stays are consider valid for a given isolate transmission-pair if stay falls within Risk Period.
* Output yielded by:
    * tools/Discipline_epiOverlap.py
* Output columns:
    1. `Overlap_event_type`
    * Possible values and their requirements:
        * `Discipline Direct (Exact)`
            * Indicates that the recipient  and donor of the isolate transmission-pair share the exact overlaping stay period within the same discipline and hospital.
        * `Discipline Direct`
            * Indicates that the recipient  and donor of the isolate transmission-pair share an overlapping stay period within the same discipline and hospital. Mutually exclusve with `Discipline Direct (Exact)`.
        * `Discipline Indirect`
            * Indicates that the recipient  and donor of the isolate transmission-pair share an non-overlapping stay period within the same discipline and hospital. Stay of donor must preceed that of the recipient.
        * `No Discipline Contact`
            * Indicates that the recipient  and donor of the isolate transmission-pair either do not share stay period within the same discipline and hospital, or stay period of the recipient entirely precedes that of the donor.
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
        * `Date_OOR` if at least one pair of recipient and donor stays is observed to be out of risk period overlap. More for trouble shooting and debugging purposes. An isolate-transmission pair with this status ONLY indicates that there are no valid stays within the risk period to determine contact.


### Adm_epiOverlap_events.tsv
* Description:
    * Event-level record for all possible valid hospital stay combinations between the recipient and donor of every isolate transmission-pair. Recipient / donor stays are considered valid for a given isolate transmission-pair if stay falls within Risk Period.
* Output yielded by:
    * tools/Adm_epiOverlap.py
* Output columns:
    1. `Hospital_Overlap_event_type`
    * Possible values and their requirements:
        * `Hospital Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same hospital.
        * `Hospital Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same hospital. Mutually exclusive with `Hospital Direct (Exact)`.
        * `Hospital Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same hospital. Stay of donor must precede that of the recipient.
        * `No Hospital Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same hospital, or the stay period of the recipient entirely precedes that of the donor.
    2. `Ward_Overlap_event_type`
    * Possible values and their requirements:
        * `Ward Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same ward and hospital.
        * `Ward Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same ward and hospital. Mutually exclusive with `Ward Direct (Exact)`.
        * `Ward Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same ward and hospital. Stay of donor must precede that of the recipient.
        * `No Ward Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same ward and hospital, or the stay period of the recipient entirely precedes that of the donor.
    3. `Bed_Overlap_event_type`
    * Possible values and their requirements:
        * `Bed Direct (Exact)`
            * Indicates that the recipient and donor of the isolate transmission-pair share the exact overlapping stay period within the same bed and hospital.
        * `Bed Direct`
            * Indicates that the recipient and donor of the isolate transmission-pair share an overlapping stay period within the same bed and hospital. Mutually exclusive with `Bed Direct (Exact)`.
        * `Bed Indirect`
            * Indicates that the recipient and donor of the isolate transmission-pair share a non-overlapping stay period within the same bed and hospital. Stay of donor must precede that of the recipient.
        * `No Bed Contact`
            * Indicates that the recipient and donor of the isolate transmission-pair either do not share a stay period within the same bed and hospital, or the stay period of the recipient entirely precedes that of the donor.
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

### Adm_epiOverlap_statuses_all_pairs.tsv
* Description:
    * Pair-level summary of all isolate transmission-pairs and their hospital, ward, and bed overlap status within the same hospital.
* Output yielded by:
    * tools/Adm_epiOverlap.py
* Analogous to the the combined information contained in the `EpiOverlap_Adm_HospSum`,  `EpiOverlap_Adm_WardSum` and `EpiOverlap_Adm_BedSum` output text files yielded by [cp_transmission_2021](https://github.com/nataschamay/cp_transmission_2021)
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
        * `Date_OOR` if at least one pair of recipient and donor stays is observed to be out of risk period overlap. More for trouble shooting and debugging purposes. An isolate-transmission pair with this status ONLY indicates that there are no valid stays within the risk period to determine contact.
