function splitCsvLine(line) {
    var values = [];
    var current = "";
    var inQuotes = false;
    var text = String(line || "");
    var i;

    for (i = 0; i < text.length; i++) {
        var ch = text.charAt(i);
        if (ch === '"') {
            if (inQuotes && i + 1 < text.length && text.charAt(i + 1) === '"') {
                current += '"';
                i++;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (ch === ',' && !inQuotes) {
            values.push(current);
            current = "";
        } else {
            current += ch;
        }
    }

    values.push(current);
    return values;
}

function parseCsv(rawText) {
    var text = String(rawText || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    var lines = text.split("\n");
    var rows = [];
    var header = null;
    var i;

    while (lines.length > 0 && String(lines[lines.length - 1]).trim() === "") {
        lines.pop();
    }

    if (lines.length === 0) {
        return rows;
    }

    header = splitCsvLine(lines[0]);
    for (i = 1; i < lines.length; i++) {
        if (String(lines[i]).trim() === "") {
            continue;
        }

        var values = splitCsvLine(lines[i]);
        var row = {};
        var c;
        for (c = 0; c < header.length; c++) {
            row[String(header[c])] = c < values.length ? values[c] : null;
        }
        rows.push(row);
    }

    return rows;
}
