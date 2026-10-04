// Native JSON.parse observations in the existing strict-UTF-8 mode (Node >=18.14).
const fs = require('fs');
const {isUtf8} = require('buffer');
const {createHash} = require('crypto');
const DEPTH_LIMIT = 64, ITEM_LIMIT = 4096, STRING_LIMIT = 4096;
const version = `Node ${process.versions.node} / V8 ${process.versions.v8}`;
function units(text) {
  const result = [];
  for (let i=0; i<text.length; i++) result.push(text.charCodeAt(i));
  return result;
}
function normalize(value, depth=0, budget={left:ITEM_LIMIT}) {
  const kind = value !== null && typeof value === 'object' ? (Array.isArray(value) ? 'array' : 'object') : null;
  const keys = kind === 'object' ? Object.keys(value) : null;
  const length = kind === 'array' ? value.length : kind === 'object' ? keys.length : 0;
  if (kind && (depth >= DEPTH_LIMIT || budget.left <= 0)) return {type:kind, truncated:true, original_length:length};
  budget.left--;
  if (value === null) return {type:'null'};
  if (typeof value === 'boolean') return {type:'boolean', value};
  if (typeof value === 'number') {
    const bytes = Buffer.alloc(8); bytes.writeDoubleBE(value);
    return {type:'float', format:'binary64', bits:bytes.toString('hex')};
  }
  if (typeof value === 'string') {
    const result = {type:'string', units:units(value.slice(0,STRING_LIMIT))};
    if (value.length > STRING_LIMIT) {
      const raw = Buffer.alloc(value.length*2);
      for (let i=0;i<value.length;i++) raw.writeUInt16BE(value.charCodeAt(i),i*2);
      Object.assign(result, {truncated:true, original_length:value.length, sha256_utf16be:createHash('sha256').update(raw).digest('hex')});
    }
    return result;
  }
  if (kind) {
    const result = {type:kind}, items = [];
    for (let i=0;i<length && budget.left>0;i++) {
      items.push(kind === 'object' ? {key:units(keys[i]), value:normalize(value[keys[i]],depth+1,budget)} : normalize(value[i],depth+1,budget));
    }
    result[kind === 'object' ? 'entries' : 'items'] = items;
    if (items.length < length) Object.assign(result,{truncated:true,original_length:length});
    return result;
  }
  return {type:'unsupported',native_type:typeof value};
}
function observe(raw) {
  const result = {status:'reject', version, parsed_value_type:null, normalized:null, key_observations:[], serialized:null,
    capabilities:{normalized:true,serialization:true,duplicate_entries:false,lookup_all_keys:false}};
  if (!isUtf8(raw)) {result.detail='Invalid UTF-8'; return result;}
  let value;
  try {value=JSON.parse(raw.toString('utf8'));}
  catch(error) {if (!(error instanceof SyntaxError)) throw error; result.detail=error.message; return result;}
  Object.assign(result,{status:'accept',parsed_value_type:value === null ? 'null' : Array.isArray(value) ? 'Array' : typeof value,normalized:normalize(value)});
  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    const keys=Object.keys(value);
    result.capabilities.lookup_all_keys=keys.length<=ITEM_LIMIT;
    result.key_observations=keys.slice(0,ITEM_LIMIT).map(key=>({key:units(key),found:Object.prototype.hasOwnProperty.call(value,key),value:normalize(value[key])}));
  }
  try {result.serialized=JSON.stringify(value);}
  catch(error) {result.serialization_error=error.message;}
  return result;
}
if (require.main === module) {
  if (typeof isUtf8 !== 'function' || process.argv.length !== 3) {process.stderr.write('Node >=18.14 and one fixture path required\n'); process.exit(2);}
  try {
    const result=observe(fs.readFileSync(process.argv[2]));
    process.stdout.write(JSON.stringify(result)+'\n');
    process.exitCode=result.status === 'accept' ? 0 : 1;
  } catch(error) {process.stderr.write(error.message+'\n'); process.exitCode=2;}
}
module.exports={observe,normalize};
