function parseIsoDate(value) {
    if (!value) {
        return null;
    }
    var text = String(value).trim();
    if (text.length >= 10) {
        return text.substring(0, 10);
    }
    return text;
}

function parseIsoDateTime(value) {
    if (!value) {
        return null;
    }
    return String(value).trim();
}

function parseHl7Timestamp(value) {
    if (!value) {
        return null;
    }
    var text = String(value).trim();
    if (text.length >= 14) {
        return text.substring(0, 4) + "-" + text.substring(4, 6) + "-" + text.substring(6, 8) + "T" + text.substring(8, 10) + ":" + text.substring(10, 12) + ":" + text.substring(12, 14);
    }
    if (text.length >= 8) {
        return text.substring(0, 4) + "-" + text.substring(4, 6) + "-" + text.substring(6, 8);
    }
    return text;
}

function parseCsvBool(value) {
    if (value === true || value === false) {
        return value;
    }
    var text = String(value || "").trim().toLowerCase();
    return text === "true" || text === "1" || text === "y" || text === "yes";
}
