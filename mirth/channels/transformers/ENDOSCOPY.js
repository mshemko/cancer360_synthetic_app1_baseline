function resolveLatestPathwayId(conn, patientId) {
    return queryScalar(
        conn,
        "SELECT pathway_id FROM cancer_pathway WHERE patient_id = ?::uuid ORDER BY updated_at DESC NULLS LAST, created_at DESC LIMIT 1",
        [patientId]
    );
}

function endoscopyStatus(row) {
    if (parseCsvBool(row['is_reported'])) {
        return 'completed';
    }
    if (String(row['exam_status'] || '').toLowerCase() === 'completed') {
        return 'in_progress';
    }
    return 'open';
}

var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var rows = parseCsv(connectorMessage.getRawData());
    var fileName = String($('originalFilename') || $('sourceFilename') || 'endoscopy.csv');
    var i;

    for (i = 0; i < rows.length; i++) {
        var row = rows[i];
        var patientId = resolvePatientId(conn, row['nhs_number']);
        if (!patientId) {
            throw 'Patient not found for endoscopy row ' + row['endoscopy_id'];
        }

        var pathwayId = resolveLatestPathwayId(conn, patientId);
        var appointmentId = deterministicUuid('endoscopy-appointment', row['endoscopy_id']);
        var actionId = deterministicUuid('endoscopy-action', row['endoscopy_id']);

        executeUpdate(conn, $('sql.appointment.upsert'), [
            appointmentId, patientId, null, row['endoscopy_id'],
            parseIsoDate(row['attendance_date'] || row['scheduled_date']), null,
            'ENDO', row['endoscopy_type'], 'endoscopy',
            String(row['exam_status'] || '').toLowerCase(), null, null,
            row['modality'], row['source_system_name'] || 'Endoscopy', row['endoscopy_id']
        ]);

        executeUpdate(conn, $('sql.cancer_action.upsert'), [
            actionId, patientId, pathwayId, 'endoscopy_report',
            row['endoscopy_type'] + ' ' + String(row['exam_status'] || '').toLowerCase(),
            String(row['endoscopy_priority'] || '').toLowerCase() === 'urgent' ? 'high' : 'normal',
            endoscopyStatus(row),
            parseIsoDate(row['report_authorised_date'] || row['attendance_date']),
            'Endoscopy', null, row['source_system_name'] || 'Endoscopy',
            row['endoscopy_report_text'], row['source_system_name'] || 'Endoscopy'
        ]);

        writeAudit(conn, {
            correlation_id: correlationId,
            event_type: 'processed',
            source_system: 'Endoscopy',
            message_type: 'csv:endoscopy',
            message_id: fileName + ':' + (i + 1),
            entity_type: 'appointment',
            entity_id: appointmentId,
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
            source_system: 'Endoscopy',
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
