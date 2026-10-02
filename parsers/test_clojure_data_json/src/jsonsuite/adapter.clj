(ns jsonsuite.adapter
  (:require [clojure.data.json :as json])
  (:import [java.io EOFException StringReader]
           [java.nio ByteBuffer]
           [java.nio.charset CharacterCodingException CodingErrorAction StandardCharsets]
           [java.nio.file Files Paths]
           [jsonsuite EofPushbackReader]))

(defn- internal-var [name]
  (get (ns-interns 'clojure.data.json) name))

(defn- complete-json? [input version]
  ;; Both versions' public read/read-str stop at the first value. Keep their
  ;; parser, but retain its pushback reader so trailing input can be checked.
  (let [reader (EofPushbackReader. (StringReader. input) 64)
        parse (internal-var '-read)]
    (if (= version "1.0.0")
      (with-bindings {(internal-var '*bigdec*) false
                      (internal-var '*key-fn*) identity
                      (internal-var '*value-fn*) (fn [_ value] value)}
        (parse reader true nil))
      (parse reader true nil @(internal-var 'default-read-options)))
    (loop [c (.read reader)]
      (cond
        (= c -1) true
        (#{9 10 13 32} c) (recur (.read reader))
        :else false))))

(defn- run [version filename]
  (let [bytes (try
                (Files/readAllBytes (Paths/get filename (make-array String 0)))
                (catch Exception error
                  (binding [*out* *err*] (println error))
                  nil))]
    (if (nil? bytes)
      2
      (try
        (let [input (-> StandardCharsets/UTF_8
                        (.newDecoder)
                        (.onMalformedInput CodingErrorAction/REPORT)
                        (.onUnmappableCharacter CodingErrorAction/REPORT)
                        (.decode (ByteBuffer/wrap bytes))
                        (.toString))]
          (try
            (if (complete-json? input version) 0 1)
            (catch Exception error
              (binding [*out* *err*] (println error))
              (let [message (or (.getMessage error) "")]
                (if (or (= (class error) Exception)
                        (instance? EOFException error)
                        (instance? NumberFormatException error)
                        (and (instance? IllegalArgumentException error)
                             (or (= "Value out of range for char: -1" message)
                                 (.startsWith message "No matching clause:"))))
                  1
                  2)))))
        (catch CharacterCodingException error
          (binding [*out* *err*] (println error))
          1)))))

(defn -main [& args]
  (System/exit
    (try
      (if (and (= (count args) 2) (#{"1.0.0" "2.2.0"} (first args)))
        (run (first args) (second args))
        (do (binding [*out* *err*]
              (println "Usage: adapter 1.0.0|2.2.0 FILE"))
            2))
      (catch Throwable error
        (binding [*out* *err*] (println error))
        2))))
