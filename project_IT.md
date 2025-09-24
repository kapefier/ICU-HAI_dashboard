 

# MONITORAGGIO NEAR REAL-TIME DELLE ICA IN TERAPIA INTENSIVA 

###### PROPOSTA DI PROTOCOLLO
###### v 0.1, 20.09.2025

Orlando Sagliocco, MD MSc(Biostat)\
UO Terapia Intensiva\
ASST Bergamo Est

<orlando.sagliocco@asst-bergamoest.it>\
<orlando.sagliocco@gmail.com>\
<https://github.com/kapefier>


## 1. Obiettivo

Automatizzare il rilevamento e la sorveglianza delle **Infezioni
Correlate all'Assistenza (ICA)** in terapia intensiva (TI), sia **core
set** (VAP, CLABSI, CAUTI, SSI) sia, in modalità stand-by, **extended
set** (LRTI, SSTI, GI, CNSI, MDR alerts), integrando EHR (Ascom
Digistat®) con elaborazione interna e output standard HL7/FHIR per
reporting e benchmark PROSAFE.

L'output finale e di facile consultabilità dovrebbe essere a mio avviso
una dashboard, del tipo dei sistemi di business intelligence (BI), il
cui aspetto potrebbe assomigliare a questo (vedi bibliografia):

![Dashboard-Esempio](/data/exampledashboard.png)


## 2. Fonti Dati

| **Fonte**              | **Dati principali**                                                                                                          | **Modalità integrazione**            |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| **Digistat EHR**       | Device (ventilatore, CVC, catetere vescicale), parametri clinici strutturati, note infermieristiche, procedure chirurgiche     | SQL diretto / API REST / feed FHIR   |
| **LIS / Microbiology** | Colture, antibiogrammi, campioni (blood, urine, respiratory)                                                                 | HL7 ORU / API FHIR                   |
| **HIS / ADT**          | Ricoveri, ingressi/uscite reparto, anagrafica paziente                                                                       | HL7 ADT / API                        |


## 3. Architettura del Flusso Dati

1.  **Feed diretto Digistat → Microservizio ETL** (ipotesi principale)[^1]

    -   Recupera dati clinici, device e microbiologia in near real-time.

2.  **Elaborazione interna**

    -   Applicazione regole cliniche per identificare eventi ICA.
    -   Generazione temporanea di eventi candidate (VAP, CLABSI, CAUTI,
        SSI).

3. **Esposizione dati**

    -   Output HL7 v2 ORU o FHIR R4 per invio a PROSAFE / dashboard.

4.  **Validazione**

    -   Controllo manuale su campione per calibrare regole automatiche.

5.  **Dashboard e reporting**

    -   BI con tassi per 1.000 device-days, trend, microrganismi più frequenti, eventi MDR.

## 4. Campi minimi da mappare


-   **Paziente**: patient\_id, data\_nascita, sesso.

-   **Ricovero**: admission\_id, reparto\_ingresso, reparto\_uscita,
    date/time.

-   **Device**: ventilatore, CVC, catetere vescicale (start/stop).


-   **Procedure chirurgiche**: tipo intervento, data.


-   **Microbiologia**: tipo campione, data prelievo, organismo,
    antibiogramma.

-   **Terapia antibiotica**: inizio/fine, farmaco, dosaggio.

-   **Segni clinici strutturati**: febbre, leucocitosi, parametri
    vitali.

## 5. Regole di identificazione

-   **CLABSI:** emocoltura positiva + CVC presente → probabilità CLABSI.


-   **VAP:** paziente ventilato ≥48h + segni clinici + coltura
    respiratoria positiva → probabilità VAP.


-   **CAUTI:** coltura urinaria positiva + catetere presente ≥48h →
    probabilità CAUTI.


-   **SSI:** post-chirurgia con coltura o diagnosi clinica entro 30--90
    giorni.


-   **Extended (stand-by):** logiche analoghe su LRTI, SSTI, GI, CNSI.

Riporto uno pseudocodice per le regole di identificazione, da tradure
poi in query SQL o Python in base alle scelte progettuali:

```bash 
INPUT:
- Lista ricoveri (patient_id, admission_id, icu_entry, icu_exit)
- Device log (device_type, start, stop)
- Microbiologia (sample_type, datetime, organism, antibiogram)
- Parametri clinici (febbre, leucociti, imaging, note cliniche)
- Procedure chirurgiche (data_intervento, tipo)
- Terapie antibiotiche (farmaco, start, stop)

PROCESS:
FOR ogni paziente IN ricoveri:
  FOR ogni evento_microbiologia associato al paziente:

    # --- CLABSI ---
    IF evento_microbiologia.sample_type == "blood" AND
       paziente ha device_type == "CVC" attivo in data evento AND
       tempo_da_inserzione >= 48h:
      genera_evento("CLABSI", evento_microbiologia)

    # --- VAP ---
    IF paziente ha device_type == "ventilatore" attivo da ≥48h AND
       evento_microbiologia.sample_type == "respiratory" AND
       criteri_clinici(febbre, leucocitosi, infiltrato_rx) == TRUE:
      genera_evento("VAP", evento_microbiologia)

    # --- CAUTI ---
    IF evento_microbiologia.sample_type == "urine" AND
       paziente ha device_type == "catetere vescicale" attivo in data evento AND
       tempo_da_inserzione >= 48h:
      genera_evento("CAUTI", evento_microbiologia)

    # --- SSI ---
    IF paziente ha intervento_chirurgico entro 30-90 giorni AND
       (evento_microbiologia positivo in sede chirurgica OR diagnosi clinica presente):
      genera_evento("SSI", evento_microbiologia)

    # --- Extended set (stand-by) ---
    IF evento_microbiologia.sample_type == "respiratory" AND NOT criteri_VAP:
      genera_evento("LRTI", evento_microbiologia, status="possible")

    IF evento_microbiologia.sample_type == "skin/soft tissue":
      genera_evento("SSTI", evento_microbiologia, status="possible")

    IF evento_microbiologia.sample_type == "stool":
      genera_evento("GI", evento_microbiologia, status="possible")

    IF evento_microbiologia.sample_type == "CSF":
      genera_evento("CNSI", evento_microbiologia, status="possible")

OUTPUT:
- Lista eventi ICA (patient_id, admission_id, tipo_evento, data, device, organismo, status)
```
 
## 6. Feed diretto e standard di interoperabilita'
- **Feed diretto Digistat:** SQL o API REST/FHIR → microservizio ETL.
- **Output standard:**  
  - HL7 ORU v2 (per legacy e PROSAFE).
  - FHIR R4 (Observation, Device, Patient) per gestione multipaziente,dashboard e invio API.
- **Vantaggi:** near real-time, standardizzato, integrabile con PROSAFE, riduce dipendenza da data warehouse aziendale.

## 7. Validazione e controllo qualita'

Ipotizzo qualcosa del genere:

-   Estrazione campione eventi automatici.

-   Revisione manuale cartelle cliniche (checklist standard).

-   Confronto automatico vs manuale → calcolo sensibilità, specificità,
    falsi positivi/negativi.

-   Iterazioni e affinamento regole.

-   Go-live limitato e monitoraggio continuo.

## 8. Strumenti e tecnologie ipotizzate

-   **Middleware / Integration engine:** Mirth Connect, Digistat API.

-   **Microservizio ETL:** Python (pandas, sqlalchemy), Node.js, o altro
    linguaggio aziendale.

-   **Standard di interoperabilità:** HL7 v2, FHIR R4.

-   **Data storage temporaneo:** filesystem sicuro o DB locale per
    elaborazioni intermedie.

-   **BI / dashboard:** web-app custom made[^2] (per me scelta consigliata), oppure Power BI, Tableau o altri prodotti commerciali.

## 9. Template mapping e checklist

### 9.1   **Mapping Digistat → PROSAFE:**
| **Campo_PROSAFE**       | **Descrizione**                | **Campo_Digistat_Esempio**       | **Note**                                  |
|-------------------------|-------------------------------|---------------------------------|------------------------------------------|
| _patient_id_              | Identificativo paziente       | admission.patient_id            | Anonimizzato/pseudonimizzato            |
| _admission_id_            | ID ricovero                   | admission.admission_id          | Collegato a degenza TI                   |
| _icu_entry_date_          | Data ingresso TI              | admission.icu_in_datetime       | Obbligatorio                             |
| _icu_exit_date_           | Data uscita TI                | admission.icu_out_datetime      | Obbligatorio                             |
| _event_id_                | ID evento ICA                 | generato algoritmo              | Progressivo                               |
| _event_date_              | Data evento ICA               | ica_events.event_datetime       | Data primo criterio positivo             |
| _event_type_              | Tipo ICA                      | ica_events.event_type           | Codice standard PROSAFE                  |
| _device_type_             | Dispositivo associato         | device_sessions.device_type     | Valorizzare se presente                  |
| _device_insertion_date_   | Data inserimento dispositivo  | device_sessions.start_datetime  | Se applicabile                           |
| _device_removal_date_     | Data rimozione dispositivo    | device_sessions.stop_datetime   | Se applicabile                           |
| _specimen_type_           | Tipo campione                 | microbiology.sample_type        | Uniformare a codici PROSAFE             |
| _specimen_date_           | Data prelievo                 | microbiology.sample_datetime    | Obbligatorio se microbiologia positiva  |
| _microorganism_           | Agente eziologico             | microbiology.organism           | Codice standard                           |
| _antibiogram_             | Profilo di resistenza         | microbiology.antibiogram        | Standard S/I/R                            |
| _ab_start_                | Inizio terapia antibiotica    | therapy.start_datetime          | Facoltativo                               |
| _ab_end_                  | Fine terapia antibiotica      | therapy.stop_datetime           | Facoltativo                               |
| _outcome_                 | Esito paziente                | admission.outcome               | Codifica standard PROSAFE                |
| _notes_                   | Note libere                   | event_notes.text                | Campi opzionali                           |


### 9.2  Checklist validazione manuale:
**Sezione A -- Identificazione evento**
-   patient\_id, admission\_id, data evento, tipo evento, devic associato

**Sezione B -- Evidenze automatiche**
-   Microbiologia positiva, criteri clinici, device presente, antibiotico somministrato. 

**Sezione C -- Revisione manuale**
-   Conferma device, segni clinici, imaging, valutazione CDC/ECDC, conclusione revisore

**Sezione D -- Confronto**
-   Concordanza automatico/manuale, commenti

**Sezione E -- Analisi aggregata**
-   Sensibilità (%), Specificità (%), Falsi positivi/negativi, azioni correttive

## 10. Appendici

### 10.1 Codice Python prototipo

Gli eventi ICA potrebbero essere prodotti come FHIR bundle, applicando le regole di identificazione ad un dataset che proviene da Digistat, di cui ancora non abbiamo i dettagli. Utilizzo un mock dataset per dimostrare la produzione del bundle.
Il codice completo può essere scaricato al seguente link [*FHIRbundle.py*](code/FHIRbundle.py).
 
Di seguito, un frammento del codice dimostrativo: 

```python
# FHIRbundle.ypinb
#
# Generazione di FHIR bundle da dati simulati
# O. Sagliocco
# --------------------------------------------

# importa le librerie

import json
from datetime import datetime
from google.colab import drive

# --- Monta Google Drive per salvare il JSON

drive.mount('/content/drive')

# --- Genera mock dati (tipo Digistat,
#     ipotetico, non abbiamo ancora accesso alla struttura dati)

patients = [
    {"patient_id": "12345", "admission_id": "A001"},
]

device_sessions = [
    {"patient_id": "12345", "device_type": "CVC",
     "start_datetime": datetime(2025, 9, 10, 12, 0),
     "stop_datetime": None},  # ancora in uso
]

microbiology_results = [
    {"patient_id": "12345", "sample_datetime": datetime(2025, 9, 20, 10, 30),
     "sample_type": "blood", "organism": "Klebsiella pneumoniae"}
]

# --- Applica Logica di definizine di una ICA
#     in questo esempio è una CLABSI

ica_events = []
for micro in microbiology_results:
    for device in device_sessions:
        if device["patient_id"] == micro["patient_id"] and device["device_type"] == "CVC":
            start = device["start_datetime"]
            stop = device["stop_datetime"] or datetime.now()
            if start <= micro["sample_datetime"] <= stop:
                ica_events.append({
                    "patient_id": micro["patient_id"],
                    "event_type": "CLABSI",
                    "event_datetime": micro["sample_datetime"],
                    "organism": micro["organism"],
                    "device_type": "CVC",
                    "device_start": start,
                    "device_stop": stop
                })

# --- Genera FHIR Bundle

fhir_bundle = {"resourceType": "Bundle", "type": "collection", "entry": []}

for event in ica_events:
    patient_ref = {"reference": f"Patient/{event['patient_id']}"}

    device_resource = {
        "resourceType": "Device",
        "id": f"device-{event['patient_id']}",
        "status": "active",
        "type": {"coding": [{"system": "http://snomed.info/sct", "code": "26412008",
                             "display": "Central venous catheter"}]},
        "patient": patient_ref,
        "period": {"start": event["device_start"].isoformat(),
                   "end": event["device_stop"].isoformat() if event["device_stop"] else None}
    }

    observation_resource = {
        "resourceType": "Observation",
        "id": f"obs-{event['patient_id']}",
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                  "code": "laboratory"}]}],
        "code": {"coding": [{"system": "http://loinc.org",
                             "code": "600-7",
                             "display": "Bacteria identified in Blood by Culture"}]},
        "subject": patient_ref,
        "effectiveDateTime": event["event_datetime"].isoformat(),
        "valueCodeableConcept": {"coding": [{"system": "http://www.whocc.no/atc",
                                             "code": event["organism"].upper().replace(" ","_"),
                                             "display": event["organism"]}]}
    }

    fhir_bundle["entry"].append({"resource": device_resource})
    fhir_bundle["entry"].append({"resource": observation_resource})
 

```
E' possibile eseguire il codice completo in Google Colaboratory: \
[![Apri in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/130KMU1Tu5Ub4w9le-nqkwKNB4U_ESFWu?usp=drive_link)

L'output generato è un file JSON contenente il bundle FHIR di una CLABSI su dati simulati, scaricabile al link
[*ica\_events\_bundle.json*](data/ica_events_bundle.json).

Una volta scaricato può essere visualizzato in un browser, la maggior ormai supportano il formato JSON, o validato con uno strumento online  tipo [*HL7 FHIR validator*](https://hl7.org/fhir/validator/).

In effetti, i passi successivi potrebbero essere:

-   Convalidare il bundle -\> \...
-   Invio a endpoint FHIR -\> \....

### 10.2 Lista delle abbreviazioni
| **Abb.** | **Descrizione** |
|----------------|----------------|
| **ADT**        | Admission, Discharge, Transfer — Messaggi HL7 che segnalano ricoveri, dimissioni e trasferimenti dei pazienti. |
| **API**        | Application Programming Interface — Interfaccia software che consente la comunicazione tra applicazioni. |
| **API REST**   | RESTful Application Programming Interface — API basata su HTTP/JSON secondo l'architettura REST. |
| **BI**         | Business Intelligence — Strumenti per analisi dati e visualizzazione dashboard. |
| **CAUTI**      | Catheter-Associated Urinary Tract Infection — Infezione urinaria associata a catetere vescicale. |
| **CDC**        | Centers for Disease Control and Prevention — Agenzia statunitense per la salute pubblica. |
| **CLABSI**     | Central Line-Associated Bloodstream Infection — Batteriemia associata a catetere venoso centrale. |
| **CNSI**       | Central Nervous System Infection — Infezione del sistema nervoso centrale (es. meningite, ventricolite). |
| **DB**         | Database — Archivio strutturato di dati, interrogabile tramite SQL. |
| **ECDC**       | European Centre for Disease Prevention and Control — Agenzia europea per la prevenzione e il controllo delle malattie. |
| **EHR**        | Electronic Health Record — Cartella clinica elettronica (es. Digistat). |
| **ETL**        | Extract, Transform, Load — Processo di estrazione, trasformazione e caricamento dei dati. |
| **FHIR**       | Fast Healthcare Interoperability Resources — Standard HL7 per interoperabilità moderna (REST/JSON/XML). |
| **GI**         | Gastrointestinal Infection — Infezione gastrointestinale (es. C. difficile). |
| **HL7**        | Health Level Seven — Famiglia di standard per interoperabilità sanitaria (HL7 v2, CDA, FHIR). |
| **ICA**        | Infezioni Correlate all'Assistenza — Infezioni acquisite durante cure e procedure sanitarie. |
| **JSON** | JavaScript Object Notation — formato per lo scambio dati basato sul linguaggio di programmazione JavaScript |
| **LIS**        | Laboratory Information System — Sistema informativo di laboratorio. |
| **LRTI**       | Lower Respiratory Tract Infection — Infezione delle basse vie respiratorie (non VAP). |
| **MDR**        | Multi-Drug Resistant — Ceppi di germi che mostrano capacità di resistenza a più di un antimicrobico. |
| **ORU**        | Observation Result Unsolicited — Messaggio HL7 v2 per trasmissione referti di laboratorio. |
| **PROSAFE**    | PROmoting SAFEty in intensive care — Programma nazionale orientato al benchmarking delle terapie intensive in Italia, con focus anche su aspetti infettivologici (petalo Infections) |
| **R4**         | Release 4 — Versione stabile e diffusa dello standard FHIR. |
| **SIR**        | Strandardazied Infection Ratio — a statistic used to track healthcare associated infections (HAIs) over time, at a national, state, or facility level. |
| **SQL**        | Structured Query Language — Linguaggio standard per interrogazione database relazionali. |
| **SSI**        | Surgical Site Infection — Infezione del sito chirurgico. |
| **SSTI**       | Skin and Soft Tissue Infection — Infezione cutanea e dei tessuti molli. |
| **TI/UTI**     | Terapia Intensiva / Unità di Terapia Intensiva — Reparto di rianimazione. |
| **VAP**        | Ventilator-Associated Pneumonia — Polmonite associata a ventilazione meccanica. |

### 10.3 Bibliografia

-   Salinas JL, Kritzman J, Kobayashi T, Edmond MB, Ince D, Diekema DJ.
    **A primer on data visualization in infection prevention and
    antimicrobial stewardship**. Infect Control Hosp Epidemiol. 2020
    Aug;41(8):948-957. <https://doi.org/10.1017/ice.2020.142>
-   The NHSN Standardized Infection Ratio (SIR). **A Guide to the SIR**; 2022.
    <https://www.cdc.gov/nhsn/pdfs/ps-analysis-resources/nhsn-sir-guide.pdf>
-   Rabiei, R., Bastani, P., Ahmadi, H. *et al.* **Developing public
    health surveillance dashboards: a scoping review on the design
    principles.** *BMC Public Health* **24**, 392 (2024).
    <https://doi.org/10.1186/s12889-024-17841-2>

[^1]:  in alternativa, si deve far uso della datawarehouse con query
    PostegreSQL

[^2]:  ad es. Tecnologia Shiny con linguaggio R o Python
