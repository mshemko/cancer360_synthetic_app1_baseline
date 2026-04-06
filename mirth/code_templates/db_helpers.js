function openCancer360Connection() {
    return DatabaseConnectionFactory.createDatabaseConnection(
        'org.postgresql.Driver',
        $('db.url'),
        $('db.username'),
        $('db.password')
    );
}

function closeQuietly(conn) {
    if (conn) {
        try {
            conn.close();
        } catch (e) {
        }
    }
}

function executeUpdate(conn, sql, params) {
    return conn.executeUpdate(sql, params);
}

function executeCachedLookup(conn, sql, params) {
    var result = conn.executeCachedQuery(sql, params);
    if (result.next()) {
        return result;
    }
    return null;
}

function queryScalar(conn, sql, params) {
    var result = executeCachedLookup(conn, sql, params);
    if (!result) {
        return null;
    }
    return String(result.getString(1));
}

function resolvePatientId(conn, nhsNumber) {
    var clean = cleanNhs(nhsNumber);
    if (!clean) {
        return null;
    }
    return queryScalar(conn, "SELECT patient_id FROM patient WHERE nhs_number = ?", [clean]);
}

function writeAudit(conn, payload) {
    var sql = [
        "INSERT INTO integration_audit_log (",
        "log_id, correlation_id, event_type, source_system, message_type,",
        "message_id, entity_type, entity_id, status, error_message,",
        "raw_payload_hash, processing_time_ms",
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?::uuid, ?, ?, ?, ?)"
    ].join(" ");

    executeUpdate(conn, sql, [
        payload.log_id || newUuid(),
        payload.correlation_id,
        payload.event_type,
        payload.source_system,
        payload.message_type,
        payload.message_id,
        payload.entity_type,
        payload.entity_id,
        payload.status,
        payload.error_message,
        payload.raw_payload_hash,
        payload.processing_time_ms || 0
    ]);
}

function writeDlq(conn, payload) {
    var sql = [
        "INSERT INTO dead_letter_queue (",
        "dlq_id, correlation_id, source_system, message_format, raw_payload,",
        "error_message, error_detail, status",
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    ].join(" ");

    executeUpdate(conn, sql, [
        payload.dlq_id || newUuid(),
        payload.correlation_id,
        payload.source_system,
        payload.message_format,
        payload.raw_payload,
        payload.error_message,
        payload.error_detail,
        payload.status || 'pending'
    ]);
}

function sha256Hex(value) {
    var digest = java.security.MessageDigest.getInstance("SHA-256");
    var bytes = digest.digest(new java.lang.String(String(value || "")).getBytes("UTF-8"));
    var sb = new java.lang.StringBuilder();
    for (var i = 0; i < bytes.length; i++) {
        var b = (bytes[i] & 0xff).toString(16);
        if (b.length() === 1) {
            sb.append('0');
        }
        sb.append(b);
    }
    return String(sb.toString());
}
