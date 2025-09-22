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

# --- Salva su Google Drive

file_path = '/content/drive/MyDrive/ica_events_bundle.json'
with open(file_path, "w") as f:
    json.dump(fhir_bundle, f, indent=2)

print(f"Bundle FHIR salvato in: {file_path}")

# --- Visualizza

print("\n--- Visualizzazione Bundle FHIR ---\n")
print(json.dumps(fhir_bundle, indent=4))

# --- Mini viewer interattivo

def view_event(bundle):
    print("\nLista pazienti/eventi disponibili:")
    for i, entry in enumerate(bundle['entry']):
        res = entry['resource']
        if res['resourceType'] == 'Observation':
            print(f"{i}: Patient {res['subject']['reference']} - {res['effectiveDateTime']} - {res['valueCodeableConcept']['coding'][0]['display']}")
    sel = input("\nSeleziona indice evento da visualizzare (ENTER per saltare): ")
    if sel.isdigit():
        idx = int(sel)
        if 0 <= idx < len(bundle['entry']):
            res = bundle['entry'][idx]['resource']
            print("\n--- Dettaglio evento selezionato ---")
            print(json.dumps(res, indent=4))
        else:
            print("Indice non valido.")
    else:
        print("Visualizzazione saltata.")

# Esegui viewer
view_event(fhir_bundle)
