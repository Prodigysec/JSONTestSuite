import java.nio.file.*;
import java.math.*;
import java.util.*;
import java.security.*;
import net.minidev.json.JSONValue;
import net.minidev.json.parser.JSONParser;
import net.minidev.json.parser.ParseException;

public class ObserveJsonSmart {
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
 public static void main(String[] args){try{run(args);}catch(Throwable e){System.err.println(e);System.exit(2);}}
 static void run(String[] args)throws Exception{
  boolean observe=args.length>0&&args[0].equals("--observe");int offset=observe?1:0;if(args.length!=offset+2){System.exit(2);return;}
  String mode=args[offset];int preset;
  switch(mode){case "default":preset=JSONParser.DEFAULT_PERMISSIVE_MODE;break;case "permissive":preset=JSONParser.MODE_PERMISSIVE;break;case "incomplete":preset=JSONParser.MODE_PERMISSIVE_WITH_INCOMPLETE;break;case "rfc4627":preset=JSONParser.MODE_RFC4627;break;case "json-simple":preset=JSONParser.MODE_JSON_SIMPLE;break;case "strictest":preset=JSONParser.MODE_STRICTEST;break;default:System.exit(2);return;}
  byte[] raw;try{raw=Files.readAllBytes(Path.of(args[offset+1]));}catch(Exception e){System.err.println(e);System.exit(2);return;}
  // Disable native stream/tail acceptance without rewriting input or changing other flags.
  int flags=preset & ~JSONParser.ACCEPT_TAILLING_DATA;
  Object value=null;ParseException rejection=null;
  JSONParser parser=new JSONParser(flags);
  try{
   value=parser.parse(raw);
   java.lang.reflect.Field bytesField=JSONParser.class.getDeclaredField("pBytes");bytesField.setAccessible(true);
   Object nativeParser=bytesField.get(parser);
   java.lang.reflect.Field positionField=Class.forName("net.minidev.json.parser.JSONParserBase").getDeclaredField("pos");positionField.setAccessible(true);
   int position=positionField.getInt(nativeParser);
   if(position<raw.length)throw new ParseException(position,ParseException.ERROR_UNEXPECTED_TOKEN,"unconsumed source bytes (including native EOI sentinel)");
  }catch(ParseException e){rejection=e;}
  int code=rejection==null?0:1;if(!observe){System.exit(code);return;}
  Map<String,Object> record=obj("status",rejection==null?"accept":"reject","version","json-smart tag v2.6.0 / ebf7cf8cf0dccef246cd1ed0d052074d787a2de4 / POM 2.6.0-SNAPSHOT / Java "+System.getProperty("java.version")+" / "+mode,
    "parsed_value_type",null,"normalized",null,"key_observations",new ArrayList<>(),"serialized",null,"capabilities",obj("normalized",true,"serialization",true,"duplicate_entries",false,"lookup_all_keys",false,"stable_object_order",false));
  if(rejection!=null)record.put("detail",rejection.toString());else{
   record.put("parsed_value_type",value==null?"null":value.getClass().getName());record.put("normalized",normalized(value));
   if(value instanceof Map){Map<?,?> map=(Map<?,?>)value;List<Object> keys=new ArrayList<>();for(Object key:map.keySet()){if(keys.size()>=4096)break;keys.add(obj("key",units((String)key),"found",map.containsKey(key),"value",normalized(map.get(key))));}record.put("key_observations",keys);((Map<String,Object>)record.get("capabilities")).put("lookup_all_keys",map.size()<=4096);}
   try{record.put("serialized",JSONValue.toJSONString(value));}catch(RuntimeException|StackOverflowError e){record.put("serialization_error",e.toString());}
  }
  System.out.println(envelope(record));System.exit(code);
 }
}
