// Validate one complete JSON text with Node.js/V8 JSON.parse.
// Reject malformed UTF-8 before Buffer.toString can replace it with U+FFFD.
const fs = require('fs');
const { isUtf8 } = require('buffer');

if (typeof isUtf8 !== 'function') {
  process.stderr.write('Node.js 18.14 or newer is required\n');
  process.exit(2);
}

if (process.argv.length !== 3) {
  process.stderr.write('expected one fixture path\n');
  process.exit(2);
}

let bytes;
try {
  bytes = fs.readFileSync(process.argv[2]);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exit(2);
}

if (!isUtf8(bytes)) {
  process.exit(1);
}

try {
  JSON.parse(bytes.toString('utf8'));
} catch (error) {
  if (error instanceof SyntaxError) {
    process.exit(1);
  }
  process.stderr.write(`${error.message}\n`);
  process.exit(2);
}
