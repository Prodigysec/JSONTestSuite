use std::env;
use std::fs;
use std::process;

fn main() {
    let mut args = env::args_os();
    let _program = args.next();
    let path = match (args.next(), args.next()) {
        (Some(path), None) => path,
        _ => process::exit(2),
    };
    let input = match fs::read(path) {
        Ok(input) => input,
        Err(_) => process::exit(2),
    };
    match serde_json::from_slice::<serde_json::Value>(&input) {
        Ok(_) => process::exit(0),
        Err(_) => process::exit(1),
    }
}
