var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var nhsNumber = cleanNhs(msg['PID']['PID.3']['PID.3.1'].toString());
    var patientId = resolvePatientId(conn, nhsNumber);
    if (!patientId) {
        throw 'Patient not found for NHS number ' + nhsNumber;
    }

    var schedule = msg['SCH'];
    var appointmentId = deterministicUuid('appointment', String(schedule['SCH.1']['SCH.1.1']));
    var startDt = parseHl7Timestamp(String(schedule['SCH.11']['SCH.11.4']));
    executeUpdate(conn, $('sql.appointment.upsert'), [
        appointmentId, patientId, null, String(schedule['SCH.1']['SCH.1.1']),
        parseIsoDate(startDt), null, 'ARIA', String(schedule['SCH.7']['SCH.7.1']),
        'oncology', String(schedule['SCH.12']['SCH.12.1']).toLowerCase(),
        null, String(schedule['SCH.16']['SCH.16.1']), String(schedule['SCH.7']['SCH.7.1']),
        'ARIA', String(msg['MSH']['MSH.10']['MSH.10.1'])
    ]);

    writeAudit(conn, {
        correlation_id: correlationId,
        event_type: 'processed',
        source_system: 'ARIA',
        message_type: messageType(msg),
        message_id: String(msg['MSH']['MSH.10']['MSH.10.1']),
        entity_type: 'appointment',
        entity_id: appointmentId,
        status: 'success',
        error_message: null,
        raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
        processing_time_ms: 0
    });
} catch (e) {
    if (conn) {
        writeDlq(conn, {
            correlation_id: correlationId,
            source_system: 'ARIA',
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
