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
	"io"
	"math"
	"os"
	"reflect"
	"runtime"
	"runtime/debug"
	"unicode/utf16"
	"unicode/utf8"

	sonic "github.com/bytedance/sonic"
	goccy "github.com/goccy/go-json"
	jsoniter "github.com/json-iterator/go"
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
func goccyNumber(raw []byte, v any) error {
	reader := bytes.NewReader(raw)
	decoder := goccy.NewDecoder(reader)
	decoder.UseNumber()
	if err := decoder.Decode(v); err != nil {
		return err
	}
	buffered, err := io.ReadAll(decoder.Buffered())
	if err != nil {
		return err
	}
	rest, err := io.ReadAll(reader)
	if err != nil {
		return err
	}
	if !whitespaceOnly(append(buffered, rest...)) {
		return errors.New("trailing input after one value")
	}
	return nil
}
func jsoniterOne(codec jsoniter.API, raw []byte, v any) error {
	iter := codec.BorrowIterator(raw)
	defer codec.ReturnIterator(iter)
	iter.ReadVal(v)
	if iter.Error != nil && iter.Error != io.EOF {
		return iter.Error
	}
	iter.WhatIsNext()
	if iter.Error == io.EOF {
		return nil
	}
	if iter.Error != nil {
		return iter.Error
	}
	return errors.New("trailing input after one value (including NUL)")
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
		fmt.Fprintln(os.Stderr, "expected mode and fixture path")
		os.Exit(2)
	}
	mode := args[0]
	var library string
	var codec api
	var decode func([]byte, any) error
	switch mode {
	case "goccy-default":
		library = "github.com/goccy/go-json"
		decode = goccy.Unmarshal
	case "goccy-number":
		library = "github.com/goccy/go-json"
		decode = goccyNumber
	case "sonic-default":
		library = "github.com/bytedance/sonic"
		codec = sonic.ConfigDefault
	case "sonic-std":
		library = "github.com/bytedance/sonic"
		codec = sonic.ConfigStd
	case "sonic-fastest":
		library = "github.com/bytedance/sonic"
		codec = sonic.ConfigFastest
	case "sonic-unicode-errors":
		library = "github.com/bytedance/sonic"
		codec = sonic.Config{ValidateString: true, UseUnicodeErrors: true}.Froze()
	case "sonic-number":
		library = "github.com/bytedance/sonic"
		codec = sonic.Config{UseNumber: true}.Froze()
	case "sonic-int64":
		library = "github.com/bytedance/sonic"
		codec = sonic.Config{UseInt64: true}.Froze()
	case "jsoniter-default":
		library = "github.com/json-iterator/go"
		codec = jsoniter.ConfigDefault
	case "jsoniter-std":
		library = "github.com/json-iterator/go"
		codec = jsoniter.ConfigCompatibleWithStandardLibrary
	case "jsoniter-fastest":
		library = "github.com/json-iterator/go"
		codec = jsoniter.ConfigFastest
	case "jsoniter-number":
		library = "github.com/json-iterator/go"
		codec = jsoniter.Config{EscapeHTML: true, UseNumber: true}.Froze()
	default:
		fmt.Fprintln(os.Stderr, "unknown mode")
		os.Exit(2)
	}
	if library == "github.com/bytedance/sonic" && sonic.APIKind != sonic.UseSonicJSON {
		fmt.Fprintln(os.Stderr, "Sonic native backend unavailable; refusing stdlib fallback")
		os.Exit(2)
	}
	if codec != nil {
		decode = codec.Unmarshal
		if library == "github.com/json-iterator/go" {
			native := codec.(jsoniter.API)
			decode = func(raw []byte, v any) error { return jsoniterOne(native, raw, v) }
		}
	}
	raw, err := os.ReadFile(args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	var value any
	err = decode(raw, &value)
	code := 0
	if err != nil {
		code = 1
	}
	if !observe {
		os.Exit(code)
	}
	record := object{"status": "reject", "version": library + " " + moduleVersion(library) + " / " + runtime.Version() + " / " + mode,
		"parsed_value_type": nil, "normalized": nil, "key_observations": []object{}, "serialized": nil,
		"capabilities": object{"normalized": true, "serialization": true, "duplicate_entries": false, "lookup_all_keys": false, "stable_object_order": false}}
	if err != nil {
		record["detail"] = err.Error()
	} else {
		record["status"] = "accept"
		nativeType := "nil"
		if value != nil {
			nativeType = reflect.TypeOf(value).String()
		}
		record["parsed_value_type"] = nativeType
		record["normalized"] = normalized(value)
		if mapping, ok := value.(map[string]any); ok {
			record["capabilities"].(object)["lookup_all_keys"] = len(mapping) <= itemLimit
			observations := []object{}
			for key := range mapping {
				if len(observations) >= itemLimit {
					break
				}
				v, found := mapping[key]
				item := object{"key": units(key), "found": found, "value": normalized(v)}
				if !utf8.ValidString(key) {
					item["invalid_native_key_utf8_hex"] = hex.EncodeToString([]byte(key))
				}
				observations = append(observations, item)
			}
			record["key_observations"] = observations
		}
		var serialized []byte
		var serializeErr error
		if codec != nil {
			serialized, serializeErr = codec.Marshal(value)
		} else {
			serialized, serializeErr = goccy.Marshal(value)
		}
		if serializeErr != nil {
			record["serialization_error"] = serializeErr.Error()
		} else {
			record["serialized"] = string(serialized)
			if !utf8.Valid(serialized) {
				record["serialized_invalid_utf8"] = true
				record["serialized_bytes_hex"] = hex.EncodeToString(serialized)
			}
		}
	}
	encoder := stdjson.NewEncoder(os.Stdout)
	if err := encoder.Encode(record); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	os.Exit(code)
}
