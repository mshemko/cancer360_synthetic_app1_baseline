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
    var resultId = deterministicUuid('pathology', accession);
    var discipline = String(msg['OBR']['OBR.4']['OBR.4.1']) === 'HISTO' ? 'histopathology' : 'haematology';
    var narrative = [];

    executeUpdate(conn, $('sql.pathology_result.upsert'), [
        resultId, patientId, accession, String(msg['OBR']['OBR.2']['OBR.2.1']),
        parseHl7Timestamp(String(msg['OBR']['OBR.7']['OBR.7.1'])),
        parseHl7Timestamp(String(msg['OBR']['OBR.14']['OBR.14.1'])),
        parseHl7Timestamp(String(msg['OBR']['OBR.22']['OBR.22.1'])),
        discipline, String(msg['OBR']['OBR.4']['OBR.4.1']), String(msg['OBR']['OBR.4']['OBR.4.2']),
        'final', String(msg['OBR']['OBR.16']['OBR.16.2']) + ' ' + String(msg['OBR']['OBR.16']['OBR.16.3']),
        null, 'ICE', String(msg['MSH']['MSH.10']['MSH.10.1']), connectorMessage.getRawData()
    ]);

    var idx = 1;
    for each (var obx in msg..OBX) {
        var valueType = String(obx['OBX.2']['OBX.2.1']);
        var value = String(obx['OBX.5']['OBX.5.1']);
        if (valueType === 'FT' || valueType === 'TX' || (valueType === 'ST' && String(obx['OBX.3']['OBX.3.1']) === 'REPORT')) {
            narrative.push(value);
        } else {
            executeUpdate(conn, $('sql.pathology_result_value.upsert'), [
                deterministicUuid('pathology-value', accession + ':' + idx),
                resultId,
                idx,
                String(obx['OBX.3']['OBX.3.1']),
                String(obx['OBX.3']['OBX.3.2']),
                valueType === 'NM' ? 'numeric' : 'coded',
                valueType === 'NM' ? value : null,
                null,
                valueType === 'NM' ? null : value,
                valueType === 'NM' ? null : value,
                String(obx['OBX.6']['OBX.6.1']),
                String(obx['OBX.7']['OBX.7.1']),
                String(obx['OBX.8']['OBX.8.1'])
            ]);
        }
        idx++;
    }

    if (narrative.length > 0) {
        executeUpdate(conn, "UPDATE pathology_result SET narrative_report = ? WHERE result_id = ?::uuid", [narrative.join('\n'), resultId]);
    }

    if (discipline === 'histopathology') {
        executeUpdate(conn, $('sql.histopath_structured.upsert'), [
            deterministicUuid('histopath', accession),
            resultId,
            patientId,
            String(msg['OBR']['OBR.4']['OBR.4.2']),
            narrative.join('\n').indexOf('grade 3') > -1 ? '3' : (narrative.join('\n').indexOf('grade 2') > -1 ? '2' : null),
            narrative.join('\n').toLowerCase().indexOf('er positive') > -1 ? 'positive' : null,
            narrative.join('\n').toLowerCase().indexOf('pr positive') > -1 ? 'positive' : null,
            narrative.join('\n').toLowerCase().indexOf('her2 negative') > -1 ? 'negative' : null,
            narrative.join('\n').toLowerCase().indexOf('ki-67 18') > -1 ? 18 : null,
            narrative.join('\n').toLowerCase().indexOf('no lymphovascular invasion') > -1 ? 'absent' : null
        ]);
    }

    writeAudit(conn, {
        correlation_id: correlationId,
        event_type: 'processed',
        source_system: 'WINPATH',
        message_type: messageType(msg),
        message_id: String(msg['MSH']['MSH.10']['MSH.10.1']),
        entity_type: 'pathology_result',
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
            source_system: 'WINPATH',
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
