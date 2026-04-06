function trackingPriority(title, text) {
    var combined = String(title || '') + ' ' + String(text || '');
    var lower = combined.toLowerCase();
    if (lower.indexOf('treatment') > -1) {
        return 'high';
    }
    if (lower.indexOf('mdt') > -1 || lower.indexOf('diagnostic') > -1) {
        return 'normal';
    }
    return 'low';
}

var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var rows = parseCsv(connectorMessage.getRawData());
    var fileName = String($('originalFilename') || $('sourceFilename') || 'somerset_tracking.csv');
    var i;

    for (i = 0; i < rows.length; i++) {
        var row = rows[i];
        var pathwayId = deterministicUuid('pathway', row['cancer_pathway_id']);
        var patientId = queryScalar(conn, "SELECT patient_id FROM cancer_pathway WHERE pathway_id = ?::uuid", [pathwayId]);
        if (!patientId) {
            throw 'No pathway found for Somerset tracking row ' + row['cancer_tracking_comment_id'];
        }

        var actionId = deterministicUuid('tracking-comment', row['cancer_tracking_comment_id']);
        var description = row['comment_title'] ? row['comment_title'] + ': ' + row['comment_text'] : row['comment_text'];

        executeUpdate(conn, $('sql.cancer_action.upsert'), [
            actionId, patientId, pathwayId, 'tracking_comment', description,
            trackingPriority(row['comment_title'], row['comment_text']), 'completed',
            parseIsoDate(row['created_at_timestamp']), 'Cancer Navigation', null,
            row['created_by'], row['comment_text'], row['source_system_name'] || 'Somerset'
        ]);

        writeAudit(conn, {
            correlation_id: correlationId,
            event_type: 'processed',
            source_system: 'Somerset',
            message_type: 'csv:tracking',
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
