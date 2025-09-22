# Near Real Time Monitoring Of Hospital Acquired Infections in the intensive Care Unit
A protocol hypothesis

## Objective
To automate the detection and surveillance of healthcare-associated infections (HAIs) in the
intensive care unit (ICU), both the core set (VAP, CLABSI, CAUTI, SSI) and, in standby mode, the extended
set (LRTI, SSTI, GI, CNSI, MDR alerts), integrating the EHR (Ascom Digistat®) with internal processing
and standard HL7/FHIR output for PROSAFE reporting and benchmarking.
The final, easily accessible output, in my opinion, should be a dashboard, similar to
business intelligence (BI) systems.

## Data Source

## Data Flow Architecture

### 1. Data Ingestion
**Direct Digistat feed → ETL microservice (main hypothesis)**  
- Retrieves clinical, device, and microbiology data in near real-time.

### 2. Internal Processing
- Applies clinical rules to identify **HAI events**.
- Temporarily generates candidate events:
  - **VAP**
  - **CLABSI**
  - **CAUTI**
  - **SSI**

### 3. Data Exposure
- Outputs via:
  - **HL7 v2 ORU**  
  - **FHIR R4**  
- Data sent to **PROSAFE/dashboard**.


### 4. Validation
- Manual sample checks to **calibrate automatic rules**.

### 5. Dashboard & Reporting
- Business Intelligence (BI) visualizations include:
  - Rates per **1,000 device days**
  - Trends over time
  - Most frequent microorganisms
  - **MDR (multi-drug resistant) events**


