use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Key, Nonce,
};
use rand::Rng;



fn generate_random_nonce() -> [u8; 12] {
    let mut nonce = [0u8; 12];
    rand::thread_rng().fill(&mut nonce);
    nonce
}

fn encrypt(data: &[u8], key: &[u8], nonce: &[u8]) -> Vec<u8> {
    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);
    let nonce = Nonce::from_slice(nonce);
    cipher.encrypt(nonce, data).unwrap()
}

fn decrypt(encrypted_data: &[u8], key: &[u8], nonce: &[u8]) -> Vec<u8> {
    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);
    let nonce = Nonce::from_slice(nonce);
    cipher.decrypt(nonce, encrypted_data).unwrap()
}

fn main() {
    // 使用32字节的密钥
    let key = "12345678901234567890123456789012";  // 32字节密钥
    let nonce = generate_random_nonce();

    // 要加密的消息
    let message = "Hello, AES Encryption!";
    println!("原始消息: {}", message);

    // 加密
    let encrypted = encrypt(message.as_bytes(), &key.as_bytes(), &nonce);
    println!("加密后数据 (hex): {}", hex::encode(&encrypted));

    // 解密
    let decrypted = decrypt(&encrypted, &key.as_bytes(), &nonce);
    let decrypted_text = String::from_utf8_lossy(&decrypted);
    println!("解密后消息: {}", decrypted_text);
}
