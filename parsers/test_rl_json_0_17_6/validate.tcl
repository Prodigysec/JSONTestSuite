# rl_json validates Tcl characters, so the Python entry point checks UTF-8 first.
if {[llength $argv] != 1} {exit 2}
lappend auto_path [lindex $argv 0]
if {[catch {package require rl_json} version] || $version ne "0.17.6"} {
    exit 2
}
fconfigure stdin -translation binary -encoding utf-8
set source [read stdin]
if {[catch {::rl_json::json valid -extensions {} $source} valid]} {
    exit 2
}
exit [expr {$valid ? 0 : 1}]
