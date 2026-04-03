"""Database seeder — populate the CDM with realistic synthetic cancer patient data.

This script bypasses the full notebook pipeline and directly seeds PostgreSQL
with clinically coherent data for the Cancer 360 PoC demonstration.
Run: python scripts/seed_database.py
"""

import asyncio
import os
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# ─── Configuration ──────────────────────────────────────────────────────────

NUM_PATIENTS = 200
BASE_DATE = date(2024, 6, 1)
TODAY = date(2025, 4, 3)

FORENAMES_F = ["Margaret","Dorothy","Patricia","Susan","Linda","Barbara","Elizabeth","Janet","Carol","Jean","Mary","Helen","Catherine","Christine","Anne","Sarah","Emma","Claire","Louise","Rachel","Hannah","Sophie","Emily","Charlotte","Amelia","Jessica","Olivia","Grace","Lily","Mia"]
FORENAMES_M = ["James","John","Robert","David","Michael","William","Richard","Thomas","Christopher","Peter","Paul","Mark","Andrew","Stephen","Alan","Brian","George","Edward","Philip","Daniel","Matthew","Adam","Oliver","Harry","Jack","Charlie","Jacob","Noah","Leo","Oscar"]
SURNAMES = ["Smith","Jones","Williams","Taylor","Brown","Davies","Evans","Wilson","Thomas","Roberts","Johnson","Lewis","Walker","Robinson","Wood","Thompson","White","Watson","Jackson","Wright","Green","Harris","Cooper","King","Lee","Clark","Baker","Hall","Allen","Young","Morris","Martin","Clarke","Anderson","Scott","Reid","Murray","Campbell"]

CANCER_TYPES = {
    "breast":     {"label":"Breast",     "icd10":"C50.4","morph":"8500/3","spec":"103","team":"Breast MDT","sex_bias":"F"},
    "colorectal": {"label":"Colorectal", "icd10":"C18.7","morph":"8140/3","spec":"104","team":"Colorectal MDT","sex_bias":None},
    "lung":       {"label":"Lung",       "icd10":"C34.1","morph":"8070/3","spec":"340","team":"Lung MDT","sex_bias":None},
    "prostate":   {"label":"Prostate",   "icd10":"C61",  "morph":"8140/3","spec":"101","team":"Prostate MDT","sex_bias":"M"},
    "gynae":      {"label":"Gynae",      "icd10":"C56",  "morph":"8441/3","spec":"502","team":"Gynae MDT","sex_bias":"F"},
    "upper_gi":   {"label":"Upper GI",   "icd10":"C16.0","morph":"8140/3","spec":"100","team":"Upper GI MDT","sex_bias":None},
    "urology":    {"label":"Urology",    "icd10":"C67.9","morph":"8120/3","spec":"101","team":"Urology MDT","sex_bias":None},
    "haem":       {"label":"Haematology","icd10":"C83.3","morph":"9680/3","spec":"370","team":"Haem MDT","sex_bias":None},
}

STAGES = ["IA","IB","IIA","IIB","IIIA","IIIB","IIIC","IV"]
TNM_MAP = {"IA":("T1","N0","M0"),"IB":("T2","N0","M0"),"IIA":("T2","N1","M0"),"IIB":("T3","N1","M0"),"IIIA":("T3","N2","M0"),"IIIB":("T4","N2","M0"),"IIIC":("T4","N3","M0"),"IV":("T4","N2","M1")}
STATUSES = ["awaiting_diagnostics","awaiting_mdt","awaiting_treatment","on_treatment","active_monitoring","completed"]
REGIMENS = {"breast":["FEC-T","AC-T","Paclitaxel weekly","TC","Trastuzumab"],"colorectal":["FOLFOX","FOLFIRI","Capecitabine"],"lung":["Carboplatin/Pemetrexed","Pembrolizumab","Osimertinib"],"prostate":["Docetaxel","Enzalutamide","Abiraterone"],"gynae":["Carboplatin/Paclitaxel"],"upper_gi":["FLOT","FOLFOX"],"urology":["Gem/Cisplatin","Pembrolizumab"],"haem":["R-CHOP","ABVD"]}
RT_PROTOCOLS = {"breast":(40,15),"colorectal":(45,25),"lung":(55,20),"prostate":(60,20),"gynae":(45,25)}


def r(a,b): return random.randint(a,b)
def rc(lst): return random.choice(lst)
def add_d(d, n): return d + timedelta(days=n)
def work_day(d):
    while d.weekday() >= 5: d += timedelta(days=1)
    return d


async def seed(database_url: str):
    engine = create_async_engine(database_url, echo=False)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print(f"Seeding {NUM_PATIENTS} patients into Cancer 360 CDM...")

    async with sf() as session:
        async with session.begin():
            ct_keys = list(CANCER_TYPES.keys())
            for i in range(NUM_PATIENTS):
                ct_key = ct_keys[i % len(ct_keys)]
                ct = CANCER_TYPES[ct_key]

                # Demographics
                if ct["sex_bias"] == "F": sex = "F"
                elif ct["sex_bias"] == "M": sex = "M"
                else: sex = rc(["M","F"])
                forename = rc(FORENAMES_F) if sex == "F" else rc(FORENAMES_M)
                surname = rc(SURNAMES)
                age = r(38, 85)
                dob = date(TODAY.year - age, r(1,12), r(1,28))

                # NHS number (10 digits total including check digit)
                base9 = f"99{i:07d}"   # 9 digits
                weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]

                total = sum(int(base9[j]) * weights[j] for j in range(9))
                rem = total % 11
                cd = 11 - rem

                if cd == 11:
                    cd = 0
                elif cd == 10:
                    base9 = f"98{i:07d}"
                    total = sum(int(base9[j]) * weights[j] for j in range(9))
                    cd = 11 - (total % 11)
                    if cd == 11:
                        cd = 0
                    elif cd == 10:
                        cd = 1

                nhs_full = base9 + str(cd)

                hosp_num = f"H{1000000+i}"
                pid = uuid.uuid4()

                # Insert patient
                await session.execute(text("""
                    INSERT INTO patient (patient_id, nhs_number, hospital_number, prefix, forename, surname,
                        date_of_birth, sex, ethnicity_code, postcode, gp_practice_code, gp_name)
                    VALUES (:pid, :nhs, :hn, :pfx, :fn, :sn, :dob, :sex, :eth, :pc, :gp, :gpn)
                    ON CONFLICT (nhs_number) DO NOTHING
                """), {
                    "pid": pid,
                    "nhs": nhs_full,
                    "hn": hosp_num,
                    "pfx": rc(["Mrs", "Ms", "Miss"]) if sex == "F" else rc(["Mr", "Dr"]),
                    "fn": forename,
                    "sn": surname,
                    "dob": dob,
                    "sex": sex,
                    "eth": rc(["A", "B", "C", "D", "H", "J", "K", "L", "M", "N"]),
                    "pc": f"{''.join(rc('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(2))}{r(1,20)} {r(1,9)}{''.join(rc('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(2))}",
                    "gp": f"B{r(80000,89999)}",
                    "gpn": f"Dr {rc(SURNAMES)}"
                })

                # Pathway timeline
                ref_date = work_day(add_d(TODAY, -r(10, 120)))
                days_on = (TODAY - ref_date).days

                stage_idx = r(0,3) if random.random() < 0.6 else r(4,7)
                stage = STAGES[stage_idx]
                tnm = TNM_MAP[stage]

                diag_date = work_day(add_d(ref_date, r(12, 25))) if days_on > 18 else None
                mdt_date = work_day(add_d(diag_date, r(3, 10))) if diag_date and days_on > 28 else None
                tx_date = work_day(add_d(mdt_date, r(8, 21))) if mdt_date and days_on > 42 else None

                if tx_date: status = rc(["on_treatment","active_monitoring","completed"])
                elif mdt_date: status = rc(["awaiting_treatment","on_treatment"])
                elif diag_date: status = rc(["awaiting_mdt","awaiting_treatment"])
                else: status = "awaiting_diagnostics"

                days_to_diag = (diag_date - ref_date).days if diag_date else None
                days_to_tx = (tx_date - ref_date).days if tx_date else None
                fds = days_to_diag is not None and days_to_diag <= 28
                rtt = days_to_tx is not None and days_to_tx <= 62

                if status == "completed": breach = "breached" if random.random()<0.15 else "none"
                elif days_on > 62 and not tx_date: breach = rc(["breached","high"])
                elif days_on > 50: breach = rc(["high","medium"])
                elif days_on > 35: breach = rc(["medium","low"])
                else: breach = rc(["none","low"])

                next_actions = {"awaiting_diagnostics":"Chase pathology results","awaiting_mdt":"Add to next MDT","awaiting_treatment":"Book theatre slot","on_treatment":"Monitor blood results","active_monitoring":"Schedule surveillance scan","completed":"Discharge to GP"}

                # Referral
                ref_id = uuid.uuid4()
                await session.execute(text("""
                    INSERT INTO referral (referral_id, patient_id, referral_date, receipt_date, clock_start_date,
                        referral_source, referral_priority, referred_to_specialty, cancer_type_code, status, source_system)
                    VALUES (:rid, :pid, :rd, :rd, :rd, 'GP', '2WW', :spec, :ct, 'open', 'e-RS')
                """), {"rid": ref_id, "pid": pid, "rd": ref_date, "spec": ct["spec"], "ct": ct_key})

                # Diagnosis
                diag_id = uuid.uuid4()
                if diag_date:
                    await session.execute(text("""
                        INSERT INTO diagnosis (diagnosis_id, patient_id, referral_id, diagnosis_date,
                            icd10_code, icd10_description, morphology_code, basis_of_diagnosis, source_system)
                        VALUES (:did, :pid, :rid, :dd, :icd, :desc, :morph, '7', 'SOMERSET')
                    """), {"did": diag_id, "pid": pid, "rid": ref_id, "dd": diag_date,
                           "icd": ct["icd10"], "desc": f"Malignant neoplasm — {ct['label'].lower()}", "morph": ct["morph"]})

                # Staging
                staging_id = uuid.uuid4()
                if diag_date:
                    await session.execute(text("""
                        INSERT INTO staging (staging_id, patient_id, diagnosis_id, staging_date, staging_type,
                            tnm_t, tnm_n, tnm_m, stage_group, grade, performance_status, source_system)
                        VALUES (:sid, :pid, :did, :sd, 'clinical', :t, :n, :m, :sg, :gr, :ps, 'SOMERSET')
                    """), {"sid": staging_id, "pid": pid, "did": diag_id, "sd": diag_date,
                           "t": tnm[0], "n": tnm[1], "m": tnm[2], "sg": stage, "gr": str(r(1,3)), "ps": r(0,2)})

                # Cancer Pathway
                pw_id = uuid.uuid4()
                await session.execute(text("""
                    INSERT INTO cancer_pathway (pathway_id, patient_id, referral_id, diagnosis_id, staging_id,
                        cancer_type_code, cancer_type_desc, date_referral_received, date_first_seen,
                        date_diagnosis, date_mdt, date_first_treatment,
                        days_to_diagnosis, days_to_treatment, fds_28day_met, standard_62day_met,
                        pathway_status, current_stage_label, next_action, next_action_date,
                        assigned_team, breach_risk, treatment_modality)
                    VALUES (:pwid, :pid, :rid, :did, :sid, :ctc, :ctd, :drr, :dfs, :dd, :dm, :dt,
                        :dtd, :dtt, :fds, :rtt, :ps, :csl, :na, :nad, :at, :br, :tm)
                """), {
                    "pwid": pw_id, "pid": pid, "rid": ref_id,
                    "did": diag_id if diag_date else None, "sid": staging_id if diag_date else None,
                    "ctc": ct_key, "ctd": ct["label"],
                    "drr": ref_date, "dfs": work_day(add_d(ref_date, r(5,12))),
                    "dd": diag_date, "dm": mdt_date, "dt": tx_date,
                    "dtd": days_to_diag, "dtt": days_to_tx, "fds": fds, "rtt": rtt,
                    "ps": status, "csl": f"{tnm[0]} {tnm[1]} {tnm[2]} — Stage {stage}" if diag_date else "Awaiting diagnosis",
                    "na": next_actions.get(status, ""), "nad": work_day(add_d(TODAY, r(1,14))),
                    "at": ct["team"], "br": breach,
                    "tm": rc(["Surgery","Chemotherapy","Radiotherapy","Chemoradiotherapy","Hormone therapy"]) if tx_date else None,
                })

                # Pathology results
                if days_on > 10:
                    pr_id = uuid.uuid4()
                    narrative = {
                        "breast": f"Core biopsies of breast tissue with infiltrating carcinoma of no special type (NST). Grade {r(1,3)}. {'Lymphovascular invasion present.' if random.random()>0.7 else 'No lymphovascular invasion.'}",
                        "colorectal": f"Colonic mucosa showing moderately differentiated adenocarcinoma infiltrating through muscularis propria.",
                        "lung": f"Bronchial biopsy: non-small cell carcinoma, favour adenocarcinoma. TTF-1 positive.",
                        "prostate": f"Prostate biopsies: {r(3,8)}/{r(10,14)} cores positive for adenocarcinoma. Gleason {rc(['3+3','3+4','4+3','4+5'])}.",
                    }.get(ct_key, f"Biopsy confirming {ct['label'].lower()} malignancy.")

                    await session.execute(text("""
                        INSERT INTO pathology_result (result_id, patient_id, source_accession, report_date,
                            discipline, test_code, test_name, status, narrative_report, source_system)
                        VALUES (:rid, :pid, :acc, :rd, 'histopathology', 'HISTO', 'Histopathology', 'final', :narr, 'ICE')
                    """), {"rid": pr_id, "pid": pid, "acc": f"H{2024000000+i}",
                           "rd": work_day(add_d(ref_date, r(8,18))), "narr": narrative})

                    # Bloods
                    bl_id = uuid.uuid4()
                    await session.execute(text("""
                        INSERT INTO pathology_result (result_id, patient_id, source_accession, report_date,
                            discipline, test_code, test_name, status, source_system)
                        VALUES (:rid, :pid, :acc, :rd, 'haematology', 'FBC', 'Full blood count', 'final', 'ICE')
                    """), {"rid": bl_id, "pid": pid, "acc": f"B{2024000000+i}", "rd": work_day(add_d(ref_date, r(3,8)))})

                # Radiology
                if days_on > 14:
                    rad_id = uuid.uuid4()
                    conclusion = "No evidence of metastatic disease." if stage_idx < 4 else rc(["Hepatic metastases identified.","Pulmonary nodules suspicious for metastases.","Suspicious bony lesion L3."])
                    await session.execute(text("""
                        INSERT INTO radiology_result (result_id, patient_id, accession_number, exam_date,
                            report_date, modality, exam_description, clinical_indication, report_text,
                            conclusion, status, source_system)
                        VALUES (:rid, :pid, :acc, :ed, :rd, 'CT', 'CT chest abdomen pelvis with contrast',
                            :ci, :rt, :con, 'verified', 'RIS')
                    """), {"rid": rad_id, "pid": pid, "acc": f"R{2024000000+i}",
                           "ed": work_day(add_d(ref_date, r(10,18))), "rd": work_day(add_d(ref_date, r(12,20))),
                           "ci": f"Staging: {ct['label'].lower()} cancer", "rt": f"Staging CT performed. {conclusion}",
                           "con": conclusion})

                # MDT
                if mdt_date:
                    await session.execute(text("""
                        INSERT INTO mdt_discussion (mdt_id, patient_id, diagnosis_id, mdt_date, mdt_site,
                            mdt_type, quorate, clinical_summary, staging_presented, decision, treatment_intent, source_system)
                        VALUES (:mid, :pid, :did, :md, :ms, 'pre_treatment', true, :cs, :sp, :dec, :ti, 'INFOFLEX')
                    """), {"mid": uuid.uuid4(), "pid": pid, "did": diag_id, "md": mdt_date, "ms": ct["team"],
                           "cs": f"{sex}, {age}y. {ct['label']} — {stage}.",
                           "sp": f"{tnm[0]} {tnm[1]} {tnm[2]}",
                           "dec": rc(["Proceed to surgery","Neoadjuvant chemotherapy","Radical chemoradiotherapy","Palliative chemotherapy","Active surveillance"]),
                           "ti": "curative" if stage_idx < 6 else "palliative"})

                # SACT
                if tx_date and random.random() > 0.4:
                    course_id = uuid.uuid4()
                    reg = rc(REGIMENS.get(ct_key, ["Chemotherapy"]))
                    n_cycles = r(2, 6)
                    await session.execute(text("""
                        INSERT INTO sact_course (course_id, patient_id, diagnosis_id, regimen_name,
                            regimen_intent, start_date, max_cycles, completed_cycles, course_status, source_system)
                        VALUES (:cid, :pid, :did, :reg, :ri, :sd, :mc, :cc, :cs, 'CHEMOCARE')
                    """), {"cid": course_id, "pid": pid, "did": diag_id, "reg": reg,
                           "ri": "adjuvant" if stage_idx < 5 else "palliative",
                           "sd": tx_date, "mc": r(4,8), "cc": n_cycles, "cs": "active" if status=="on_treatment" else "completed"})

                    for c in range(n_cycles):
                        await session.execute(text("""
                            INSERT INTO sact_cycle (cycle_id, course_id, patient_id, cycle_number, start_date,
                                bsa_m2, performance_status, cycle_outcome, delay_days, dose_reduction_pct, source_system)
                            VALUES (:cyid, :cid, :pid, :cn, :sd, :bsa, :ps, :co, :dd, :dr, 'CHEMOCARE')
                        """), {"cyid": uuid.uuid4(), "cid": course_id, "pid": pid, "cn": c+1,
                               "sd": work_day(add_d(tx_date, c * 21)),
                               "bsa": Decimal(str(round(random.uniform(1.5, 2.2), 2))),
                               "ps": r(0,1), "co": "completed", "dd": r(0,3) if c>1 else 0,
                               "dr": rc([0,0,0,0,15,25]) if c>2 else 0})

                # RT
                if tx_date and random.random() > 0.5 and ct_key in RT_PROTOCOLS:
                    proto = RT_PROTOCOLS[ct_key]
                    rt_id = uuid.uuid4()
                    await session.execute(text("""
                        INSERT INTO radiotherapy_course (course_id, patient_id, diagnosis_id, treatment_intent,
                            treatment_site, technique, total_dose_gy, fractions_prescribed, dose_per_fraction_gy,
                            first_fraction_date, machine_id, course_status, source_system)
                        VALUES (:rid, :pid, :did, :ti, :ts, :tech, :td, :fp, :dpf, :ffd, :mid, :cs, 'MOSAIQ')
                    """), {"rid": rt_id, "pid": pid, "did": diag_id,
                           "ti": "radical" if stage_idx<5 else "palliative",
                           "ts": ct["label"], "tech": rc(["VMAT","IMRT","3DCRT"]),
                           "td": Decimal(str(proto[0])), "fp": proto[1],
                           "dpf": Decimal(str(round(proto[0]/proto[1], 2))),
                           "ffd": work_day(add_d(tx_date, r(0,30))),
                           "mid": rc(["LA1","LA2","LA3","LA4"]),
                           "cs": "active" if status=="on_treatment" else "completed"})

                if (i+1) % 50 == 0:
                    print(f"  Seeded {i+1}/{NUM_PATIENTS} patients...")

    print(f"Done. Seeded {NUM_PATIENTS} patients with full cancer pathway data.")
    await engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://cancer360:localdev@localhost:5432/cancer360")
    asyncio.run(seed(db_url))
