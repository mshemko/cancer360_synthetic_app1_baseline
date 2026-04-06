function deterministicUuid(namespace, value) {
    var input = String(namespace || "") + ":" + String(value || "");
    var bytes = new java.lang.String(input).getBytes("UTF-8");
    return java.util.UUID.nameUUIDFromBytes(bytes).toString();
}

function newUuid() {
    return java.util.UUID.randomUUID().toString();
}
