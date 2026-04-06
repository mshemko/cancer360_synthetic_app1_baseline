function meetingCacheKey(meetingId) {
    return 'somerset.mdt.' + String(meetingId || '');
}

function detectMdtFileKind(fileName) {
    var text = String(fileName || '').toLowerCase();
    if (text.indexOf('somerset_mdt_meetings_') > -1) {
        return 'meetings';
    }
    if (text.indexOf('somerset_mdt_bookings_') > -1) {
        return 'bookings';
    }
    if (text.indexOf('somerset_mdt_notes_') > -1) {
        return 'notes';
    }
    return 'unknown';
}

function cacheMeeting(meetingId, timestamp, status) {
    globalMap.put(meetingCacheKey(meetingId), String(timestamp || '') + '|' + String(status || ''));
}

function getCachedMeeting(meetingId) {
    var value = globalMap.get(meetingCacheKey(meetingId));
    if (!value) {
        return null;
    }
    var parts = String(value).split('|');
    return {
        meeting_timestamp: parts.length > 0 ? parts[0] : null,
        mdt_status: parts.length > 1 ? parts[1] : null
    };
}

function resolvePathwayContext(conn, sourcePathwayId) {
    var pathwayId = deterministicUuid('pathway', sourcePathwayId);
    var result = executeCachedLookup(
        conn,
        "SELECT patient_id, diagnosis_id, cancer_type_desc FROM cancer_pathway WHERE pathway_id = ?::uuid",
        [pathwayId]
    );
    if (!result) {
        return null;
    }
    return {
        pathway_id: pathwayId,
        patient_id: String(result.getString(1)),
        diagnosis_id: result.getString(2) ? String(result.getString(2)) : null,
        cancer_type_desc: result.getString(3) ? String(result.getString(3)) : 'Cancer'
    };
}

function inferTreatmentIntent(noteText) {
    var lower = String(noteText || '').toLowerCase();
    if (lower.indexOf('palliative') > -1) {
        return 'palliative';
    }
    if (lower.indexOf('surgery') > -1 || lower.indexOf('radiotherapy') > -1 || lower.indexOf('chemotherapy') > -1 || lower.indexOf('definitive') > -1) {
        return 'curative';
    }
    return null;
}

var conn = null;
var correlationId = newUuid();
try {
    conn = openCancer360Connection();
    var fileName = String($('originalFilename') || $('sourceFilename') || 'somerset_mdt.csv');
    var fileKind = detectMdtFileKind(fileName);
    var rows = parseCsv(connectorMessage.getRawData());
    var i;

    for (i = 0; i < rows.length; i++) {
        var row = rows[i];

        if (fileKind === 'meetings') {
            cacheMeeting(row['mdt_meeting_id'], row['meeting_timestamp'], row['mdt_status']);
            writeAudit(conn, {
                correlation_id: correlationId,
                event_type: 'processed',
                source_system: 'Somerset',
                message_type: 'csv:mdt_meetings',
                message_id: fileName + ':' + (i + 1),
                entity_type: 'mdt_meeting_cache',
                entity_id: deterministicUuid('mdt-meeting-cache', row['mdt_meeting_id']),
                status: 'success',
                error_message: null,
                raw_payload_hash: sha256Hex(connectorMessage.getRawData()),
                processing_time_ms: 0
            });
            continue;
        }

        var sourcePathwayId = fileKind === 'bookings' ? row['pathway_id'] : row['cancer_pathway_id'];
        var context = resolvePathwayContext(conn, sourcePathwayId);
        if (!context) {
            throw 'No pathway context found for MDT row in file ' + fileName + ' pathway ' + sourcePathwayId;
        }

        var meetingId = row['meeting_id'];
        var meeting = getCachedMeeting(meetingId);
        if (!meeting) {
            throw 'No cached meeting metadata found for meeting ' + meetingId;
        }

        var discussionId = deterministicUuid('mdt-discussion', meetingId + ':' + sourcePathwayId);
        var noteText = fileKind === 'notes' ? row['mdt_note_text'] : null;

        executeUpdate(conn, $('sql.mdt_discussion.upsert'), [
            discussionId,
            context.patient_id,
            context.diagnosis_id,
            parseIsoDate(meeting.meeting_timestamp),
            context.cancer_type_desc,
            'site_mdt',
            String(meeting.mdt_status || '').toLowerCase() !== 'cancelled',
            noteText,
            null,
            noteText,
            inferTreatmentIntent(noteText),
            row['source_system_name'] || row['source_system_names'] || 'Somerset',
            meetingId
        ]);

        writeAudit(conn, {
            correlation_id: correlationId,
            event_type: 'processed',
            source_system: 'Somerset',
            message_type: fileKind === 'bookings' ? 'csv:mdt_bookings' : 'csv:mdt_notes',
            message_id: fileName + ':' + (i + 1),
            entity_type: 'mdt_discussion',
            entity_id: discussionId,
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
