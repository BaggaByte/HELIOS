use aes_gcm::{
    aead::{Aead, AeadCore, KeyInit, OsRng},
    Aes256Gcm, Key, Nonce,
};
use base64::{engine::general_purpose::STANDARD, Engine as _};
use std::fs;
use std::path::Path;

#[tauri::command]
pub fn encrypt_file(file_path: String, base64_key: String) -> Result<String, String> {
    log::info!("Encrypting file: {}", file_path);

    // Decode key
    let key_bytes = STANDARD.decode(&base64_key).map_err(|e| e.to_string())?;
    if key_bytes.len() != 32 {
        return Err("Key must be exactly 32 bytes (256 bits)".to_string());
    }

    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng); // 96-bits; unique per message

    // Read file
    let path = Path::new(&file_path);
    if !path.exists() {
        return Err(format!("File not found: {}", file_path));
    }
    
    let data = fs::read(path).map_err(|e| e.to_string())?;

    // Encrypt
    let ciphertext = cipher.encrypt(&nonce, data.as_ref()).map_err(|e| e.to_string())?;

    // Combine nonce + ciphertext
    let mut encrypted_data = nonce.to_vec();
    encrypted_data.extend_from_slice(&ciphertext);

    // Write back to a new file
    let out_path = format!("{}.enc", file_path);
    fs::write(&out_path, encrypted_data).map_err(|e| e.to_string())?;

    log::info!("Successfully encrypted to: {}", out_path);
    
    // Optionally delete original, but let's keep it safe for MVP
    
    Ok(out_path)
}
