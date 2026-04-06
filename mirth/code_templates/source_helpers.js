function sendingApplication(msg) {
    try {
        return String(msg['MSH']['MSH.3']['MSH.3.1'].toString());
    } catch (e) {
        return null;
    }
}

function messageType(msg) {
    try {
        return String(msg['MSH']['MSH.9']['MSH.9.1'].toString()) + "^" + String(msg['MSH']['MSH.9']['MSH.9.2'].toString());
    } catch (e) {
        return null;
    }
}

function filePrefix(fileName) {
    if (!fileName) {
        return null;
    }
    var idx = String(fileName).indexOf("_");
    return idx === -1 ? String(fileName) : String(fileName).substring(0, idx);
}

function cleanNhs(value) {
    if (!value) {
        return null;
    }
    return String(value).replace(/[\s-]/g, "").substring(0, 10);
}
