use wasm_bindgen::prelude::*;
use aes::Aes256;
use cipher::{
    KeyIvInit, BlockEncryptMut, BlockDecryptMut,
    generic_array::GenericArray,
    Block, BlockSizeUser
};

#[wasm_bindgen]
pub fn encrypt(data: &str, key: &str) -> String {
    // 将密钥转换为32字节数组（AES-256需要32字节密钥）
    let key = hex::decode(key).unwrap();
    let key = GenericArray::from_slice(&key);
    
    // 生成随机IV（初始化向量）
    let mut iv = [0u8; 16];
    getrandom::getrandom(&mut iv).unwrap();
    let iv = GenericArray::from_slice(&iv);
    
    // 准备明文数据
    let data = data.as_bytes();
    
    // 使用PKCS7填充
    let padding_len = 16 - (data.len() % 16);
    let mut padded_data = Vec::from(data);
    padded_data.extend(std::iter::repeat(padding_len as u8).take(padding_len));
    
    // 加密数据
    let mut cipher = cbc::Encryptor::<Aes256>::new(key, iv);
    let mut blocks = Vec::new();
    for chunk in padded_data.chunks(16) {
        let mut block = Block::<Aes256>::default();
        block.copy_from_slice(chunk);
        blocks.push(block);
    }
    cipher.encrypt_blocks_mut(&mut blocks);
    
    // 将IV和密文合并并转换为十六进制字符串
    let mut result = Vec::new();
    result.extend_from_slice(iv);
    for block in blocks {
        result.extend_from_slice(&block);
    }
    hex::encode(result)
}

#[wasm_bindgen]
pub fn decrypt(encrypted_data: &str, key: &str) -> Result<String, JsValue> {
    // 将密钥转换为32字节数组
    let key = hex::decode(key).map_err(|_| JsValue::from_str("Invalid key format"))?;
    let key = GenericArray::from_slice(&key);
    
    // 解码加密数据
    let encrypted = hex::decode(encrypted_data)
        .map_err(|_| JsValue::from_str("Invalid encrypted data format"))?;
    
    if encrypted.len() < 16 {
        return Err(JsValue::from_str("Invalid encrypted data length"));
    }
    
    // 分离IV和密文
    let (iv, ciphertext) = encrypted.split_at(16);
    let iv = GenericArray::from_slice(iv);
    
    // 解密数据
    let mut cipher = cbc::Decryptor::<Aes256>::new(key, iv);
    let mut blocks = Vec::new();
    for chunk in ciphertext.chunks(16) {
        let mut block = Block::<Aes256>::default();
        block.copy_from_slice(chunk);
        blocks.push(block);
    }
    cipher.decrypt_blocks_mut(&mut blocks);
    
    // 将blocks转换回字节向量
    let mut buf = Vec::new();
    for block in blocks {
        buf.extend_from_slice(&block);
    }
    
    // 移除PKCS7填充
    if let Some(&padding_len) = buf.last() {
        if padding_len as usize <= buf.len() {
            buf.truncate(buf.len() - padding_len as usize);
        }
    }
    
    // 转换为字符串
    String::from_utf8(buf)
        .map_err(|_| JsValue::from_str("Invalid UTF-8 sequence"))
}

// 生成一个随机的AES-256密钥
#[wasm_bindgen]
pub fn generate_key() -> String {
    let mut key = [0u8; 32];
    getrandom::getrandom(&mut key).unwrap();
    hex::encode(key)
}
