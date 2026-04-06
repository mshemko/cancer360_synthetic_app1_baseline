function iptStatus(row) {
    if (parseCsvBool(row['is_returned'])) {
        return 'completed';
    }
    if (parseCsvBool(row['is_received'])) {
        return 'in_progress';
    }
    return 'open';
}

function iptNotes(row) {
    var parts = [];
    if (row['tertiary_sending_comment']) {
        parts.push('Sending comment: ' + row['tertiary_sending_comment']);
    }
    if (row['tertiary_return_comment']) {
        parts.push('Return comment: ' + row['tertiary_return_comment']);
    }
    return parts.join('\n');
}

var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var rows = parseCsv(connectorMessage.getRawData());
    var fileName = String($('originalFilename') || $('sourceFilename') || 'somerset_ipt.csv');
    var i;

    for (i = 0; i < rows.length; i++) {
        var row = rows[i];
        var patientId = resolvePatientId(conn, row['nhs_number']);
        if (!patientId) {
            throw 'Patient not found for IPT row ' + row['tertiary_id'];
        }

        var pathwayId = row['pathway_id'] ? deterministicUuid('pathway', row['pathway_id']) : null;
        var actionId = deterministicUuid('ipt-action', row['tertiary_id']);
        executeUpdate(conn, $('sql.cancer_action.upsert'), [
            actionId, patientId, pathwayId, 'inter_provider_transfer',
            'IPT to ' + row['receiving_org_name'] + ' for ' + row['tertiary_reason'],
            'high', iptStatus(row), parseIsoDate(row['tertiary_received_date'] || row['tertiary_sent_date']),
            row['receiving_org_name'], null, row['sending_org_name'], iptNotes(row),
            row['source_system_name'] || 'Somerset'
        ]);

        writeAudit(conn, {
            correlation_id: correlationId,
            event_type: 'processed',
            source_system: 'Somerset',
            message_type: 'csv:ipt',
            message_id: fileName + ':' + (i + 1),
            entity_type: 'cancer_action',
            entity_id: actionId,
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
