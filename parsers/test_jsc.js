// JavaScriptCore's jsc shell accepts a path after -- in arguments[0].
if (arguments.length !== 1) {
    print('JSONTESTSUITE_ADAPTER_ERROR');
    quit();
}

let text;
try {
    text = readFile(arguments[0]);
} catch (error) {
    print('JSONTESTSUITE_ADAPTER_ERROR');
    quit();
}

try {
    JSON.parse(text);
    print('JSONTESTSUITE_ACCEPT');
} catch (error) {
    if (error instanceof SyntaxError) {
        print('JSONTESTSUITE_REJECT');
    } else {
        print('JSONTESTSUITE_ADAPTER_ERROR');
    }
}
