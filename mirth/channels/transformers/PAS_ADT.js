var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var msgType = messageType(msg);
    var nhsNumber = cleanNhs(msg['PID']['PID.3']['PID.3.1'].toString());
    var hospitalNumber = msg['PID']['PID.3'][1] ? String(msg['PID']['PID.3'][1]['PID.3.1']) : null;
    var surname = String(msg['PID']['PID.5']['PID.5.1']);
    var forename = String(msg['PID']['PID.5']['PID.5.2']);
    var prefix = String(msg['PID']['PID.5']['PID.5.5']);
    var dob = parseHl7Timestamp(String(msg['PID']['PID.7']['PID.7.1']));
    var sex = String(msg['PID']['PID.8']['PID.8.1'] || 'X');
    var patientId = deterministicUuid('patient', nhsNumber);

    executeUpdate(conn, $('sql.patient.upsert'), [
        patientId, nhsNumber, hospitalNumber, prefix, forename, surname,
        parseIsoDate(dob), sex, null, null, null, null
    ]);

    var entityType = 'patient';
    var entityId = patientId;
    if (msgType === 'ADT^A01' || msgType === 'ADT^A03') {
        var episodeId = deterministicUuid('episode', String(msg['MSH']['MSH.10']['MSH.10.1']));
        executeUpdate(conn, $('sql.episode.upsert'), [
            episodeId, patientId, null, String(msg['MSH']['MSH.10']['MSH.10.1']),
            'inpatient', parseIsoDate(parseHl7Timestamp(String(msg['MSH']['MSH.7']['MSH.7.1']))),
            null, 'Surgical Oncology', String(msg['PV1']['PV1.3']['PV1.3.1']),
            null, null, 'PAS', String(msg['MSH']['MSH.10']['MSH.10.1'])
        ]);
        entityType = 'episode';
        entityId = episodeId;
    }

    writeAudit(conn, {
        correlation_id: correlationId,
        event_type: 'processed',
        source_system: 'CERNER',
        message_type: msgType,
        message_id: String(msg['MSH']['MSH.10']['MSH.10.1']),
        entity_type: entityType,
        entity_id: entityId,
        status: 'success',
        error_message: null,
        raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
        processing_time_ms: 0
    });
} catch (e) {
    if (conn) {
        writeDlq(conn, {
            correlation_id: correlationId,
            source_system: 'CERNER',
            message_format: 'hl7',
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
