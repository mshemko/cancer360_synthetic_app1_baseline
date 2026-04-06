function toInteger(value) {
    if (value === null || value === undefined || String(value).trim() === '') {
        return null;
    }
    return java.lang.Integer.valueOf(String(value));
}

function toDecimal(value) {
    if (value === null || value === undefined || String(value).trim() === '') {
        return null;
    }
    return java.math.BigDecimal.valueOf(java.lang.Double.valueOf(String(value)));
}

function latestDiagnosisId(conn, patientId) {
    return queryScalar(
        conn,
        "SELECT diagnosis_id FROM diagnosis WHERE patient_id = ?::uuid ORDER BY diagnosis_date DESC NULLS LAST, created_at DESC LIMIT 1",
        [patientId]
    );
}

function minDate(rows, key) {
    var value = null;
    var i;
    for (i = 0; i < rows.length; i++) {
        var current = parseIsoDate(rows[i][key]);
        if (current && (!value || current < value)) {
            value = current;
        }
    }
    return value;
}

function maxDate(rows, key) {
    var value = null;
    var i;
    for (i = 0; i < rows.length; i++) {
        var current = parseIsoDate(rows[i][key]);
        if (current && (!value || current > value)) {
            value = current;
        }
    }
    return value;
}

function lowerText(value) {
    return String(value || '').toLowerCase();
}

var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var rows = parseCsv(connectorMessage.getRawData());
    var fileName = String($('originalFilename') || $('sourceFilename') || 'aria_treatment.csv');
    var groups = {};
    var i;

    for (i = 0; i < rows.length; i++) {
        var row = rows[i];
        var key = String(row['treatment_group_id']);
        if (!groups[key]) {
            groups[key] = [];
        }
        groups[key].push(row);
    }

    for (var groupId in groups) {
        var groupRows = groups[groupId];
        var first = groupRows[0];
        var patientId = resolvePatientId(conn, first['nhs_number']);
        if (!patientId) {
            throw 'Patient not found for Aria treatment group ' + groupId;
        }

        var diagnosisId = latestDiagnosisId(conn, patientId);
        if (lowerText(first['treatment_type']) === 'radiotherapy') {
            var rtCourseId = deterministicUuid('rt-course', groupId);
            var deliveredFractions = 0;
            for (i = 0; i < groupRows.length; i++) {
                if (lowerText(groupRows[i]['treatment_status']) === 'attended') {
                    deliveredFractions++;
                }
            }

            executeUpdate(conn, $('sql.radiotherapy_course.upsert'), [
                rtCourseId, patientId, diagnosisId, groupId, 'radical',
                first['treatment_site'], 'VMAT', toDecimal(first['total_dose_gy']),
                toInteger(first['fractions_prescribed']), toDecimal(first['dose_per_fraction_gy']),
                minDate(groupRows, 'scheduled_date'), maxDate(groupRows, 'scheduled_date'),
                parseIsoDate(first['ordered_date']), parseIsoDate(first['ordered_date']), first['consultant_name'],
                first['machine_id'], null, false,
                deliveredFractions >= toInteger(first['fractions_prescribed']) ? 'completed' : 'active',
                null, first['consultant_name'], 'RYJ', first['source_system_name'] || 'ARIA'
            ]);

            for (i = 0; i < groupRows.length; i++) {
                row = groupRows[i];
                executeUpdate(conn, $('sql.radiotherapy_fraction.upsert'), [
                    deterministicUuid('rt-fraction', row['cancer_treatment_id']),
                    rtCourseId,
                    toInteger(row['fraction_number']),
                    parseIsoDate(row['scheduled_date']),
                    lowerText(row['treatment_status']) === 'attended' ? parseIsoDate(row['attendance_date']) : null,
                    null,
                    toDecimal(row['dose_per_fraction_gy']),
                    lowerText(row['treatment_status']) === 'attended' ? 'delivered' : 'scheduled',
                    row['machine_id'],
                    row['treatment_description']
                ]);
            }

            writeAudit(conn, {
                correlation_id: correlationId,
                event_type: 'processed',
                source_system: 'ARIA',
                message_type: 'csv:radiotherapy',
                message_id: fileName + ':' + groupId,
                entity_type: 'radiotherapy_course',
                entity_id: rtCourseId,
                status: 'success',
                error_message: null,
                raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
                processing_time_ms: 0
            });
        } else {
            var courseId = deterministicUuid('sact-course', groupId);
            var cycleSeen = {};
            var completedCycles = 0;
            for (i = 0; i < groupRows.length; i++) {
                if (lowerText(groupRows[i]['treatment_status']) === 'attended') {
                    completedCycles++;
                }
            }

            executeUpdate(conn, $('sql.sact_course.upsert'), [
                courseId, patientId, diagnosisId, groupId, first['regimen_name'],
                null, lowerText(first['treatment_type']) === 'immunotherapy' ? 'palliative' : 'curative',
                minDate(groupRows, 'scheduled_date'), maxDate(groupRows, 'scheduled_date'),
                toInteger(first['max_cycles']), toInteger(completedCycles),
                completedCycles >= toInteger(first['max_cycles']) ? 'completed' : 'active',
                null, null, first['consultant_name'], 'RYJ', first['source_system_name'] || 'ARIA'
            ]);

            for (i = 0; i < groupRows.length; i++) {
                row = groupRows[i];
                var cycleNumber = String(row['cycle_number']);
                var cycleId = deterministicUuid('sact-cycle', groupId + ':' + cycleNumber);

                if (!cycleSeen[cycleNumber]) {
                    executeUpdate(conn, $('sql.sact_cycle.upsert'), [
                        cycleId, courseId, patientId, toInteger(row['cycle_number']),
                        parseIsoDate(row['scheduled_date']), parseIsoDate(row['attendance_date']),
                        toDecimal(row['height_cm']), toDecimal(row['weight_kg']), toDecimal(row['bsa_m2']),
                        null, lowerText(row['treatment_status']), 0, 0, null, null,
                        row['source_system_name'] || 'ARIA'
                    ]);
                    cycleSeen[cycleNumber] = true;
                }

                executeUpdate(conn, $('sql.sact_drug.upsert'), [
                    deterministicUuid('sact-drug', row['cancer_treatment_id']),
                    cycleId, row['drug_name'], null, toDecimal(row['dose_mg']),
                    row['bsa_m2'] ? toDecimal(java.lang.Double.valueOf(String(row['dose_mg'])) / java.lang.Double.valueOf(String(row['bsa_m2']))) : null,
                    row['dose_unit'], 100, row['route'],
                    parseIsoDate(row['attendance_date'] || row['scheduled_date']), null
                ]);
            }

            writeAudit(conn, {
                correlation_id: correlationId,
                event_type: 'processed',
                source_system: 'ARIA',
                message_type: 'csv:sact',
                message_id: fileName + ':' + groupId,
                entity_type: 'sact_course',
                entity_id: courseId,
                status: 'success',
                error_message: null,
                raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
                processing_time_ms: 0
            });
        }
    }
} catch (e) {
    if (conn) {
        writeDlq(conn, {
            correlation_id: correlationId,
            source_system: 'ARIA',
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
