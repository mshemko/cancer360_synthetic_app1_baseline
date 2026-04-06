function daysBetween(startDate, endDate) {
    if (!startDate || !endDate) {
        return null;
    }
    var start = java.time.LocalDate.parse(String(startDate));
    var end = java.time.LocalDate.parse(String(endDate));
    return java.lang.Long.valueOf(java.time.temporal.ChronoUnit.DAYS.between(start, end)).intValue();
}

function nextPathwayAction(row) {
    if (!row['diagnosis_date']) {
        return 'Complete diagnostic pathway';
    }
    if (!row['decision_to_treat_date']) {
        return 'Review at MDT and record decision to treat';
    }
    if (!row['first_treatment_date']) {
        return 'Book first treatment';
    }
    return 'Pathway complete';
}

function nextPathwayActionDate(row) {
    if (!row['diagnosis_date']) {
        return parseIsoDate(row['28_day_breach_date']);
    }
    if (!row['first_treatment_date'] && row['decision_to_treat_date']) {
        return parseIsoDate(row['31_day_breach_date']);
    }
    if (!row['first_treatment_date']) {
        return parseIsoDate(row['62_day_breach_date']);
    }
    return null;
}

function breachRisk(row) {
    if (String(row['pathway_status'] || '').toLowerCase() === 'closed') {
        return 'none';
    }
    var breachDate = nextPathwayActionDate(row);
    if (!breachDate) {
        return 'low';
    }

    var today = java.time.LocalDate.now();
    var due = java.time.LocalDate.parse(String(breachDate));
    var days = java.lang.Long.valueOf(java.time.temporal.ChronoUnit.DAYS.between(today, due)).intValue();
    if (days < 0) {
        return 'breached';
    }
    if (days <= 7) {
        return 'high';
    }
    if (days <= 14) {
        return 'medium';
    }
    return 'low';
}

var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var rows = parseCsv(connectorMessage.getRawData());
    var fileName = String($('originalFilename') || $('sourceFilename') || 'somerset_pathways.csv');
    var i;

    for (i = 0; i < rows.length; i++) {
        var row = rows[i];
        var nhsNumber = cleanNhs(row['nhs_number']);
        if (!nhsNumber) {
            throw 'Missing NHS number in Somerset pathways row ' + (i + 1);
        }

        var patientId = deterministicUuid('patient', nhsNumber);
        var pathwayId = deterministicUuid('pathway', row['pathway_id']);
        var referralId = deterministicUuid('referral', row['pathway_id']);
        var diagnosisId = row['diagnosis_date'] || row['diagnosis_icd_10_code'] || row['diagnosis'] ? deterministicUuid('diagnosis', row['pathway_id']) : null;

        executeUpdate(conn, $('sql.patient.upsert'), [
            patientId, nhsNumber, row['mrn'], null, row['first_name'], row['surname'],
            parseIsoDate(row['date_of_birth']), null, null, null, null, null
        ]);

        executeUpdate(conn, $('sql.referral.upsert'), [
            referralId, patientId, row['pathway_id'], parseIsoDate(row['referral_received_date']),
            parseIsoDate(row['referral_received_date']), parseIsoDate(row['adjusted_pathway_start_date'] || row['original_pathway_start_date']),
            row['referral_source'], row['pathway_referral_route'], row['cancer_site'],
            String(row['pathway_status'] || 'open').toLowerCase(), 'Somerset'
        ]);

        if (diagnosisId) {
            executeUpdate(conn, $('sql.diagnosis.upsert'), [
                diagnosisId, patientId, referralId, parseIsoDate(row['diagnosis_date']),
                row['diagnosis_icd_10_code'], row['diagnosis'], null, null,
                'somerset_pathway', 'Somerset'
            ]);
        }

        executeUpdate(conn, $('sql.cancer_pathway.upsert'), [
            pathwayId, patientId, referralId, diagnosisId, null,
            row['cancer_site'], row['diagnosis'] || row['cancer_site'], parseIsoDate(row['referral_received_date']),
            parseIsoDate(row['first_seen_date']), parseIsoDate(row['diagnosis_date']), null,
            parseIsoDate(row['decision_to_treat_date']), parseIsoDate(row['first_treatment_date']),
            daysBetween(row['referral_received_date'], row['first_seen_date']),
            daysBetween(row['referral_received_date'], row['diagnosis_date']),
            daysBetween(row['referral_received_date'], row['first_treatment_date']),
            row['diagnosis_date'] ? daysBetween(row['referral_received_date'], row['diagnosis_date']) <= 28 : null,
            row['first_treatment_date'] ? daysBetween(row['referral_received_date'], row['first_treatment_date']) <= 62 : null,
            row['first_treatment_date'] && row['decision_to_treat_date'] ? daysBetween(row['decision_to_treat_date'], row['first_treatment_date']) <= 31 : null,
            row['first_treatment_type'], row['first_treatment_type'],
            String(row['pathway_status'] || 'open').toLowerCase(), row['pathway_status'],
            nextPathwayAction(row), nextPathwayActionDate(row),
            row['cancer_site'] + ' MDT', 'Cancer Navigator', breachRisk(row),
            'Imported from Somerset Cancer Register'
        ]);

        writeAudit(conn, {
            correlation_id: correlationId,
            event_type: 'processed',
            source_system: 'Somerset',
            message_type: 'csv:pathways',
            message_id: fileName + ':' + (i + 1),
            entity_type: 'cancer_pathway',
            entity_id: pathwayId,
            status: 'success',
            error_message: null,
            raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
            processing_time_ms: 0
        });
    }
} catch (e) {
    if (conn) {
        writeDlq(conn, {
            correlation_id: correlationId,
            source_system: 'Somerset',
            message_format: 'csv',
            raw_payload: connectorMessage.getRawData(),
            error_message: String(e),
            error_detail: Packages.org.apache.commons.lang3.exception.ExceptionUtils.getStackTrace(e),
            status: 'pending'
        });
    }
    throw e;
} finally {
    closeQuietly(conn);
}
