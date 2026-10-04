import java.nio.file.*;
import java.math.*;
import java.util.*;
import java.security.*;
import java.lang.reflect.*;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONException;
import com.alibaba.fastjson.parser.*;
import com.alibaba.fastjson.util.IOUtils;
import com.owlike.genson.*;
import com.owlike.genson.stream.*;
import com.jsoniter.JsonIterator;
import com.jsoniter.output.JsonStream;
import com.jsoniter.spi.JsonException;

public class ObserveJavaBatch03 {
 static Map<String,Object> obj(Object... fields){Map<String,Object> m=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)m.put((String)fields[i],fields[i+1]);return m;}
 static List<Integer> units(String s){List<Integer> r=new ArrayList<>();for(int i=0;i<s.length();i++)r.add((int)s.charAt(i));return r;}
 static Object tree(Object v,int depth,int[] budget)throws Exception {
  String kind=v instanceof Map?"object":v instanceof List?"array":null;
  int length=v instanceof Map?((Map<?,?>)v).size():v instanceof List?((List<?>)v).size():0;
  if(kind!=null&&(depth>=64||budget[0]<=0))return obj("type",kind,"truncated",true,"original_length",length);
  budget[0]--;
  if(v==null)return obj("type","null");
  if(v instanceof Boolean)return obj("type","boolean","value",v);
  if(v instanceof String){String s=(String)v;Map<String,Object> r=obj("type","string","units",units(s.substring(0,Math.min(s.length(),4096))));if(s.length()>4096){byte[] b=new byte[s.length()*2];for(int i=0;i<s.length();i++){b[2*i]=(byte)(s.charAt(i)>>8);b[2*i+1]=(byte)s.charAt(i);}r.putAll(obj("truncated",true,"original_length",s.length(),"sha256_utf16be",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b))));}return r;}
  if(v instanceof BigDecimal)return obj("type","decimal","text",v.toString());
  if(v instanceof Float)return obj("type","float","format","binary32","bits",String.format("%08x",Float.floatToRawIntBits((Float)v)));
  if(v instanceof Double)return obj("type","float","format","binary64","bits",String.format("%016x",Double.doubleToRawLongBits((Double)v)));
  if(v instanceof Number)return obj("type","integer","decimal",v.toString());
  if(v instanceof Map){List<Object> entries=new ArrayList<>();for(Map.Entry<?,?> e:((Map<?,?>)v).entrySet()){if(budget[0]<=0)break;entries.add(obj("key",units((String)e.getKey()),"value",tree(e.getValue(),depth+1,budget)));}Map<String,Object> r=obj("type","object","entries",entries);if(entries.size()<length)r.putAll(obj("truncated",true,"original_length",length));return r;}
  if(v instanceof List){List<Object> items=new ArrayList<>();for(Object child:(List<?>)v){if(budget[0]<=0)break;items.add(tree(child,depth+1,budget));}Map<String,Object> r=obj("type","array","items",items);if(items.size()<length)r.putAll(obj("truncated",true,"original_length",length));return r;}
  return obj("type","unsupported","native_type",v.getClass().getName());
 }
 static Object normalized(Object v)throws Exception{return tree(v,0,new int[]{4096});}
 // Independent envelope writer preserves native UTF-16 text, including lone surrogates.
 static String quote(String s){StringBuilder b=new StringBuilder("\"");for(int i=0;i<s.length();i++){char c=s.charAt(i);if(c=='"'||c=='\\'){b.append('\\').append(c);}else if(c<32||c>=127){b.append(String.format("\\u%04x",(int)c));}else b.append(c);}return b.append('"').toString();}
 static String envelope(Object v){if(v==null)return "null";if(v instanceof String)return quote((String)v);if(v instanceof Boolean||v instanceof Integer||v instanceof Long)return v.toString();if(v instanceof List){List<String> parts=new ArrayList<>();for(Object x:(List<?>)v)parts.add(envelope(x));return "["+String.join(",",parts)+"]";}if(v instanceof Map){List<String> parts=new ArrayList<>();for(Map.Entry<?,?> e:((Map<?,?>)v).entrySet())parts.add(quote((String)e.getKey())+":"+envelope(e.getValue()));return "{"+String.join(",",parts)+"}";}throw new IllegalArgumentException("unsupported observation envelope type");}
 static Genson genson;
 static Object parse(String mode,byte[] raw)throws Exception {
  if(mode.startsWith("fastjson-")){
   int flags=JSON.DEFAULT_PARSER_FEATURE;
   switch(mode){
    case "fastjson-default":break;
    case "fastjson-extension-flags-off":flags=Feature.AutoCloseSource.mask|Feature.UseBigDecimal.mask;break;
    case "fastjson-comments":flags|=Feature.AllowComment.mask;break;
    case "fastjson-double":flags&=~Feature.UseBigDecimal.mask;break;
    default:throw new IllegalArgumentException("Unknown mode");
   }
   // Use the library's own byte decoder; its public parse(byte[]) returns null on decoding failure.
   char[] chars=new char[raw.length];int length=IOUtils.decodeUTF8(raw,0,raw.length,chars);
   if(length<0)throw new JSONException("native UTF-8 decoding failed");
   ParserConfig config=new ParserConfig();config.setSafeMode(true);
   DefaultJSONParser parser=new DefaultJSONParser(chars,length,config,flags);
   try{
    if(parser.lexer.token()==JSONToken.EOF)throw new JSONException("No native value token");
    Object value=parser.parse();parser.handleResovleTask(value);
    Field position=JSONLexerBase.class.getDeclaredField("bp");position.setAccessible(true);
    int consumed=position.getInt(parser.lexer);
    if(consumed<0||consumed>length+1)throw new IllegalStateException("Native cursor outside decoded source");
    if(consumed<length)throw new JSONException("Unconsumed source characters, including native EOI sentinel");
    return value;
   }finally{parser.close();}
  }
  if(mode.startsWith("genson-")){
   switch(mode){case "genson-default":case "genson-utf8":genson=new Genson();break;case "genson-strict-double":genson=new GensonBuilder().useStrictDoubleParse(true).create();break;default:throw new IllegalArgumentException("Unknown mode");}
   // Require a value-bearing input; native empty input is reported as null.
   boolean blank=true;for(byte b:raw)if(b!=32&&b!=9&&b!=10&&b!=13){blank=false;break;}
   if(blank)throw new JsonStreamException("No value-bearing input");
   ObjectReader reader=mode.equals("genson-default")?genson.createReader(raw):genson.createReader(new ByteArrayInputStream(raw),StandardCharsets.UTF_8);
   Object value=genson.deserialize(GenericType.of(Object.class),reader,new Context(genson));
   // hasNext() can return false for non-value trailing punctuation. Require actual native EOF.
   Method next=JsonReader.class.getDeclaredMethod("readNextToken",boolean.class);next.setAccessible(true);
   int token;
   try{token=(Integer)next.invoke(reader,false);}catch(InvocationTargetException e){
    Throwable cause=e.getCause();if(cause instanceof JsonStreamException)throw (JsonStreamException)cause;
    if(cause instanceof Error)throw (Error)cause;
    throw e;
   }
   if(token!=-1)throw new JsonStreamException("Trailing input after native value");
   return value;
  }
  if(mode.equals("jsoniter-default")){
   JsonIterator iterator=JsonIterator.parse(raw);Object value=iterator.read();
   Field field=JsonIterator.class.getDeclaredField("head");field.setAccessible(true);int consumed=field.getInt(iterator);
   if(consumed<0||consumed>raw.length)throw new IllegalStateException("Native cursor outside byte input");
   for(int i=consumed;i<raw.length;i++)if(raw[i]!=32&&raw[i]!=9&&raw[i]!=10&&raw[i]!=13)throw new JsonException("Trailing input after native value");
   return value;
  }
  throw new IllegalArgumentException("Unknown mode");
 }
 static String serialize(String mode,Object value){
  if(mode.startsWith("fastjson-"))return JSON.toJSONString(value);
  if(mode.startsWith("genson-"))return genson.serialize(value);
  return value==null?JsonStream.serialize(com.jsoniter.spi.TypeLiteral.create(Object.class),value):JsonStream.serialize(value);
 }
 static String version(String mode){
  String lib=mode.startsWith("fastjson-")?"Fastjson "+JSON.VERSION+" / SafeMode":mode.startsWith("genson-")?"Genson 1.6 (checksum-pinned release artifact)":"jsoniter Java 0.9.23 (checksum-pinned release artifact; generic read; reflection serializer)";
  return lib+" / Java "+System.getProperty("java.version")+" / "+mode;
 }
 public static void main(String[] args){try{run(args);}catch(Throwable e){System.err.println(e);System.exit(2);}}
 static void run(String[] args)throws Exception{
  boolean observe=args.length>0&&args[0].equals("--observe");int offset=observe?1:0;
  if(args.length!=offset+2){System.exit(2);return;}
  String mode=args[offset];byte[] raw=Files.readAllBytes(Path.of(args[offset+1]));Object value=null;String rejection=null;
  try{value=parse(mode,raw);}catch(JSONException|JsonBindingException|JsonStreamException|JsonException e){rejection=e.toString();}
  int code=rejection==null?0:1;if(!observe){System.exit(code);return;}
  Map<String,Object> record=obj("status",rejection==null?"accept":"reject","version",version(mode),
    "parsed_value_type",null,"normalized",null,"key_observations",new ArrayList<>(),"serialized",null,
    "capabilities",obj("normalized",true,"serialization",true,"duplicate_entries",false,"lookup_all_keys",false,"stable_object_order",false));
  if(rejection!=null)record.put("detail",rejection);else{
   record.put("parsed_value_type",value==null?"null":value.getClass().getName());record.put("normalized",normalized(value));
   if(value instanceof Map){Map<?,?> map=(Map<?,?>)value;List<Object> keys=new ArrayList<>();for(Object key:map.keySet()){if(keys.size()>=4096)break;keys.add(obj("key",units((String)key),"found",map.containsKey(key),"value",normalized(map.get(key))));}record.put("key_observations",keys);((Map<String,Object>)record.get("capabilities")).put("lookup_all_keys",map.size()<=4096);}
   try{record.put("serialized",serialize(mode,value));}catch(RuntimeException|StackOverflowError e){record.put("serialization_error",e.toString());}
  }
  System.out.println(envelope(record));System.exit(code);
 }
}
