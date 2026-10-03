// Observe parsed values separately from JSON.stringify's output.
const fs = require('fs');
const { isUtf8 } = require('buffer');

if (process.argv.length !== 4 || !['zero', 'keys', 'survey'].includes(process.argv[2])) {
  process.stderr.write('expected a kind and fixture path\n');
  process.exit(2);
}

let bytes;
try {
  bytes = fs.readFileSync(process.argv[3]);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exit(2);
}
if (typeof isUtf8 !== 'function' || !isUtf8(bytes)) {
  process.stderr.write('strict UTF-8 decoding unavailable or failed\n');
  process.exit(typeof isUtf8 === 'function' && process.argv[2] === 'survey' ? 1 : 2);
}

let value;
try {
  value = JSON.parse(bytes.toString('utf8'));
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exit(1);
}

let observation;
if (process.argv[2] === 'survey') {
  observation = { value_type: value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value };
} else if (process.argv[2] === 'zero') {
  if (!Array.isArray(value) || value.length !== 1 || typeof value[0] !== 'number' || value[0] !== 0) {
    process.stderr.write('expected a one-element zero array\n');
    process.exit(2);
  }
  observation = { negative_zero: Object.is(value[0], -0) };
} else {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    process.stderr.write('expected an object\n');
    process.exit(2);
  }
  observation = { members: Object.entries(value) };
}
observation.status = 'ok';
observation.serialized = JSON.stringify(value);
process.stdout.write(`${JSON.stringify(observation)}\n`);
