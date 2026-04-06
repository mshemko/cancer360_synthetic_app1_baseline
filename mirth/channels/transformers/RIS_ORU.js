var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var nhsNumber = cleanNhs(msg['PID']['PID.3']['PID.3.1'].toString());
    var patientId = resolvePatientId(conn, nhsNumber);
    if (!patientId) {
        throw 'Patient not found for NHS number ' + nhsNumber;
    }

    var accession = String(msg['OBR']['OBR.3']['OBR.3.1']);
    var resultId = deterministicUuid('radiology', accession);
    var reportLines = [];
    var conclusionLines = [];
    for each (var obx in msg..OBX) {
        var code = String(obx['OBX.3']['OBX.3.1']);
        var value = String(obx['OBX.5']['OBX.5.1']);
        if (code === 'CONCLUSION') {
            conclusionLines.push(value);
        } else {
            reportLines.push(value);
        }
    }

    executeUpdate(conn, $('sql.radiology_result.upsert'), [
        resultId, patientId, accession, String(msg['OBR']['OBR.2']['OBR.2.1']),
        parseHl7Timestamp(String(msg['OBR']['OBR.7']['OBR.7.1'])),
        parseHl7Timestamp(String(msg['OBR']['OBR.22']['OBR.22.1'])),
        String(msg['OBR']['OBR.4']['OBR.4.1']), String(msg['OBR']['OBR.4']['OBR.4.1']),
        String(msg['OBR']['OBR.4']['OBR.4.2']), reportLines.join('\n'),
        conclusionLines.join('\n'), String(msg['OBR']['OBR.16']['OBR.16.2']) + ' ' + String(msg['OBR']['OBR.16']['OBR.16.3']),
        'verified', 'RIS', String(msg['MSH']['MSH.10']['MSH.10.1']), connectorMessage.getRawData()
    ]);

    writeAudit(conn, {
        correlation_id: correlationId,
        event_type: 'processed',
        source_system: 'CRIS',
        message_type: messageType(msg),
        message_id: String(msg['MSH']['MSH.10']['MSH.10.1']),
        entity_type: 'radiology_result',
        entity_id: resultId,
        status: 'success',
        error_message: null,
        raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
        processing_time_ms: 0
    });
} catch (e) {
    if (conn) {
        writeDlq(conn, {
            correlation_id: correlationId,
            source_system: 'CRIS',
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
