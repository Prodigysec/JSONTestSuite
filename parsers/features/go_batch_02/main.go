// Observe native interfaces; encoding/json only writes the observation envelope.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	stdjson "encoding/json"
	"errors"
	"fmt"
	"strings"

	"math"
	"os"
	"reflect"
	"runtime"
	"runtime/debug"
	"unicode/utf16"
	"unicode/utf8"

	jp "github.com/buger/jsonparser"
	"github.com/francoispqt/gojay"
)

const depthLimit = 64
const itemLimit = 4096
const stringLimit = 4096

type object = map[string]any
type api interface {
	Unmarshal([]byte, any) error
	Marshal(any) ([]byte, error)
}

func units(s string) []uint16 { return utf16.Encode([]rune(s)) }
func stringNode(s string) object {
	u := units(s)
	n := object{"type": "string", "units": u}
	if !utf8.ValidString(s) {
		n["invalid_native_utf8_hex"] = hex.EncodeToString([]byte(s))
	}
	if len(u) > stringLimit {
		raw := make([]byte, len(u)*2)
		for i, v := range u {
			binary.BigEndian.PutUint16(raw[2*i:], v)
		}
		sum := sha256.Sum256(raw)
		n["units"] = u[:stringLimit]
		n["truncated"] = true
		n["original_length"] = len(u)
		n["sha256_utf16be"] = hex.EncodeToString(sum[:])
	}
	return n
}
func normalize(v any, depth int, budget *int) object {
	if depth >= depthLimit || *budget <= 0 {
		switch x := v.(type) {
		case []any:
			return object{"type": "array", "truncated": true, "original_length": len(x)}
		case map[string]any:
			return object{"type": "object", "truncated": true, "original_length": len(x)}
		}
	}
	*budget--
	switch x := v.(type) {
	case nil:
		return object{"type": "null"}
	case bool:
		return object{"type": "boolean", "value": x}
	case string:
		return stringNode(x)
	case float64:
		raw := make([]byte, 8)
		binary.BigEndian.PutUint64(raw, math.Float64bits(x))
		return object{"type": "float", "format": "binary64", "bits": hex.EncodeToString(raw)}
	case int64:
		return object{"type": "integer", "decimal": fmt.Sprint(x)}
	case stdjson.Number:
		return object{"type": "number-lexeme", "text": string(x)}
	case []any:
		items := []object{}
		for _, child := range x {
			if *budget <= 0 {
				break
			}
			items = append(items, normalize(child, depth+1, budget))
		}
		n := object{"type": "array", "items": items}
		if len(items) < len(x) {
			n["truncated"] = true
			n["original_length"] = len(x)
		}
		return n
	case map[string]any:
		entries := []object{}
		for key, child := range x {
			if *budget <= 0 {
				break
			}
			entry := object{"key": units(key), "value": normalize(child, depth+1, budget)}
			if !utf8.ValidString(key) {
				entry["invalid_native_key_utf8_hex"] = hex.EncodeToString([]byte(key))
			}
			entries = append(entries, entry)
		}
		n := object{"type": "object", "entries": entries}
		if len(entries) < len(x) {
			n["truncated"] = true
			n["original_length"] = len(x)
		}
		return n
	default:
		return object{"type": "unsupported", "native_type": reflect.TypeOf(v).String()}
	}
}
func normalized(v any) object { budget := itemLimit; return normalize(v, 0, &budget) }
func whitespaceOnly(raw []byte) bool {
	for _, b := range raw {
		if b != ' ' && b != '\t' && b != '\r' && b != '\n' {
			return false
		}
	}
	return true
}

// ordered objects retain native callback traversal, including duplicate entries.
type member struct {
	key   string
	value any
}
type members []member

func tree(v any, depth int, budget *int) object {
	switch x := v.(type) {
	case members:
		if depth >= depthLimit || *budget <= 0 {
			return object{"type": "object", "truncated": true, "original_length": len(x)}
		}
		*budget--
		entries := []object{}
		for _, entry := range x {
			if *budget <= 0 {
				break
			}
			item := object{"key": units(entry.key), "value": tree(entry.value, depth+1, budget)}
			if !utf8.ValidString(entry.key) {
				item["invalid_native_key_utf8_hex"] = hex.EncodeToString([]byte(entry.key))
			}
			entries = append(entries, item)
		}
		n := object{"type": "object", "entries": entries}
		if len(entries) < len(x) {
			n["truncated"] = true
			n["original_length"] = len(x)
		}
		return n
	case []any:
		if depth >= depthLimit || *budget <= 0 {
			return object{"type": "array", "truncated": true, "original_length": len(x)}
		}
		*budget--
		items := []object{}
		for _, child := range x {
			if *budget <= 0 {
				break
			}
			items = append(items, tree(child, depth+1, budget))
		}
		n := object{"type": "array", "items": items}
		if len(items) < len(x) {
			n["truncated"] = true
			n["original_length"] = len(x)
		}
		return n
	default:
		return normalize(v, depth, budget)
	}
}
func observedTree(v any) object { budget := itemLimit; return tree(v, 0, &budget) }
func nativeJSONParser(cfg jp.Config, raw []byte) (any, error) {
	value, kind, end, err := cfg.Get(raw)
	if err != nil {
		return nil, err
	}
	if end < 0 || end > len(raw) || !whitespaceOnly(raw[end:]) {
		return nil, errors.New("trailing input after one native value")
	}
	switch kind {
	case jp.Null:
		return nil, nil
	case jp.Boolean:
		return jp.ParseBoolean(value)
	case jp.Number:
		if _, err := jp.ParseFloat(value); err != nil {
			return nil, err
		}
		return stdjson.Number(string(value)), nil
	case jp.String:
		return cfg.GetString(raw)
	case jp.Object:
		entries := members{}
		err = cfg.ObjectEach(raw, func(key, value []byte, kind jp.ValueType, end int) error {
			start := end - len(value)
			if kind == jp.String {
				start -= 2
			}
			if start < 0 || end > len(raw) {
				return errors.New("native callback offset outside source")
			}
			child, e := nativeJSONParser(cfg, raw[start:end])
			if e != nil {
				return e
			}
			entries = append(entries, member{string(key), child})
			return nil
		})
		return entries, err
	case jp.Array:
		children := []any{}
		var childErr error
		_, err = cfg.ArrayEach(raw, func(value []byte, kind jp.ValueType, start int, e error) {
			if childErr != nil {
				return
			}
			if e != nil {
				childErr = e
				return
			}
			end := start + len(value)
			if kind == jp.String {
				start -= 2
			}
			if start < 0 || end > len(raw) {
				childErr = errors.New("native callback offset outside source")
				return
			}
			child, e := nativeJSONParser(cfg, raw[start:end])
			if e != nil {
				childErr = e
				return
			}
			children = append(children, child)
		})
		if childErr != nil {
			return nil, childErr
		}
		return children, err
	default:
		return nil, errors.New("unsupported native value type")
	}
}
func captured(raw []byte) ([]byte, error) {
	d := gojay.NewDecoder(bytes.NewReader(raw))
	var token gojay.EmbeddedJSON
	if err := d.Decode(&token); err != nil {
		return nil, err
	}
	// Read only the pinned decoder's position: gojay exposes no public consumed-offset API.
	position := reflect.ValueOf(d).Elem().FieldByName("cursor")
	if !position.IsValid() || position.Kind() != reflect.Int {
		panic("gojay decoder layout changed")
	}
	end := int(position.Int())
	if end < 0 || end > len(raw) {
		panic("gojay cursor outside input")
	}
	if !whitespaceOnly(raw[end:]) {
		return nil, errors.New("trailing input after native value")
	}
	if len(token) == 0 {
		return nil, errors.New("no native value captured")
	}
	return token, nil
}

type gojayObject struct{ entries members }

func (v *gojayObject) NKeys() int { return 0 }
func (v *gojayObject) UnmarshalJSONObject(d *gojay.Decoder, key string) error {
	var token gojay.EmbeddedJSON
	if err := d.EmbeddedJSON(&token); err != nil {
		return err
	}
	child, err := nativeGojay(token)
	if err != nil {
		return err
	}
	v.entries = append(v.entries, member{key, child})
	return nil
}

type gojayArray struct{ items []any }

func (v *gojayArray) UnmarshalJSONArray(d *gojay.Decoder) error {
	var token gojay.EmbeddedJSON
	if err := d.EmbeddedJSON(&token); err != nil {
		return err
	}
	child, err := nativeGojay(token)
	if err != nil {
		return err
	}
	v.items = append(v.items, child)
	return nil
}
func nativeGojay(raw []byte) (any, error) {
	token, err := captured(raw)
	if err != nil {
		return nil, err
	}
	switch token[0] {
	case '{':
		v := &gojayObject{entries: members{}}
		err = gojay.UnmarshalJSONObject(token, v)
		return v.entries, err
	case '[':
		v := &gojayArray{items: []any{}}
		err = gojay.UnmarshalJSONArray(token, v)
		return v.items, err
	case '"':
		var v string
		err = gojay.Unmarshal(token, &v)
		return v, err
	case 't', 'f':
		var v bool
		err = gojay.Unmarshal(token, &v)
		return v, err
	case 'n':
		return nil, nil
	default:
		var v float64
		err = gojay.Unmarshal(token, &v)
		return v, err
	}
}

type gojayObjectWriter struct {
	entries members
	err     error
}

func (v *gojayObjectWriter) IsNil() bool { return false }
func (v *gojayObjectWriter) MarshalJSONObject(e *gojay.Encoder) {
	for _, entry := range v.entries {
		raw, err := serializeGojay(entry.value)
		if err != nil {
			v.err = err
			return
		}
		token := gojay.EmbeddedJSON(raw)
		e.AddEmbeddedJSONKey(entry.key, &token)
	}
}

type gojayArrayWriter struct {
	items []any
	err   error
}

func (v *gojayArrayWriter) IsNil() bool { return false }
func (v *gojayArrayWriter) MarshalJSONArray(e *gojay.Encoder) {
	for _, child := range v.items {
		raw, err := serializeGojay(child)
		if err != nil {
			v.err = err
			return
		}
		token := gojay.EmbeddedJSON(raw)
		e.AddEmbeddedJSON(&token)
	}
}
func serializeGojay(v any) ([]byte, error) {
	switch x := v.(type) {
	case members:
		writer := &gojayObjectWriter{entries: x}
		raw, err := gojay.MarshalJSONObject(writer)
		if writer.err != nil {
			return nil, writer.err
		}
		return raw, err
	case []any:
		writer := &gojayArrayWriter{items: x}
		raw, err := gojay.MarshalJSONArray(writer)
		if writer.err != nil {
			return nil, writer.err
		}
		return raw, err
	case nil:
		token := gojay.EmbeddedJSON("null")
		return gojay.Marshal(&token)
	default:
		return gojay.Marshal(v)
	}
}

func moduleVersion(module string) string {
	if info, ok := debug.ReadBuildInfo(); ok {
		for _, dependency := range info.Deps {
			if dependency.Path == module {
				return dependency.Version
			}
		}
	}
	return "unavailable"
}
func main() {
	observe := false
	args := os.Args[1:]
	if len(args) > 0 && args[0] == "--observe" {
		observe = true
		args = args[1:]
	}
	if len(args) != 2 {
		os.Exit(2)
	}
	mode := args[0]
	raw, err := os.ReadFile(args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	var cfg jp.Config
	var library string
	var value any
	switch mode {
	case "jsonparser-default":
		cfg = jp.DefaultConfig
		library = "github.com/buger/jsonparser"
	case "jsonparser-lenient":
		cfg = jp.Lenient
		library = "github.com/buger/jsonparser"
	case "jsonparser-single-quotes":
		cfg = jp.Config{AllowSingleQuotes: true}
		library = "github.com/buger/jsonparser"
	case "jsonparser-unknown-escapes":
		cfg = jp.Config{AllowUnknownEscapes: true}
		library = "github.com/buger/jsonparser"
	case "gojay-native":
		library = "github.com/francoispqt/gojay"
	default:
		fmt.Fprintln(os.Stderr, "unknown mode")
		os.Exit(2)
	}
	if strings.HasPrefix(mode, "jsonparser") {
		value, err = nativeJSONParser(cfg, raw)
	} else {
		value, err = nativeGojay(raw)
	}
	code := 0
	if err != nil {
		code = 1
	}
	if !observe {
		os.Exit(code)
	}
	record := object{"status": "reject", "version": library + " " + moduleVersion(library) + " / " + runtime.Version() + " / " + mode, "parsed_value_type": nil, "normalized": nil, "key_observations": []object{}, "serialized": nil,
		"capabilities": object{"normalized": true, "serialization": false, "duplicate_entries": true, "lookup_all_keys": false, "stable_object_order": true}}
	if err != nil {
		record["detail"] = err.Error()
	} else {
		record["status"] = "accept"
		nativeType := "nil"
		if value != nil {
			nativeType = reflect.TypeOf(value).String()
		}
		if library == "github.com/buger/jsonparser" {
			_, nativeKind, _, nativeErr := cfg.Get(raw)
			if nativeErr != nil {
				panic("accepted tree lost native root type")
			}
			nativeType = "jsonparser." + nativeKind.String() + " (native token/callback API)"
		} else {
			if _, ok := value.(members); ok {
				nativeType = "gojay native object callbacks"
			}
			if _, ok := value.([]any); ok {
				nativeType = "gojay native array callbacks"
			}
		}
		record["parsed_value_type"] = nativeType
		record["normalized"] = observedTree(value)
		if entries, ok := value.(members); ok && strings.HasPrefix(mode, "jsonparser") {
			observations := []object{}
			seen := map[string]bool{}
			for _, entry := range entries {
				if seen[entry.key] {
					continue
				}
				seen[entry.key] = true
				v, kind, _, e := cfg.Get(raw, entry.key)
				found := e == nil
				item := object{"key": units(entry.key), "found": found}
				if !utf8.ValidString(entry.key) {
					item["invalid_native_key_utf8_hex"] = hex.EncodeToString([]byte(entry.key))
				}
				if found {
					var lookup any
					var lookupErr error
					if kind == jp.String {
						lookup, lookupErr = cfg.GetString(raw, entry.key)
					} else {
						lookup, lookupErr = nativeJSONParser(cfg, v)
					}
					if lookupErr != nil {
						item["found"] = false
						item["lookup_error"] = lookupErr.Error()
					} else {
						item["value"] = observedTree(lookup)
					}
				}
				observations = append(observations, item)
				if len(observations) >= itemLimit {
					break
				}
			}
			record["key_observations"] = observations
			record["capabilities"].(object)["lookup_all_keys"] = len(seen) < itemLimit
		}
		if library == "github.com/francoispqt/gojay" {
			b, e := serializeGojay(value)
			record["capabilities"].(object)["serialization"] = true
			if e != nil {
				record["serialization_error"] = e.Error()
			} else {
				record["serialized"] = string(b)
				if !utf8.Valid(b) {
					record["serialized_invalid_utf8"] = true
					record["serialized_bytes_hex"] = hex.EncodeToString(b)
				}
			}
		}
	}
	if e := stdjson.NewEncoder(os.Stdout).Encode(record); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(2)
	}
	os.Exit(code)
}
