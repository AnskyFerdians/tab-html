/**
 * WhatsApp Sticker Formatter & Converter
 * Converts images/buffers to WhatsApp compatible WebP stickers using Sharp.
 */

const sharp = require('sharp');

/**
 * Convert any image buffer to a WhatsApp sticker WebP buffer (512x512)
 * @param {Buffer} inputBuffer 
 * @param {Object} options 
 * @returns {Promise<Buffer>}
 */
async function createSticker(inputBuffer, options = {}) {
    const pack = options.pack || 'Antigravity Bot';
    const author = options.author || 'AI Assistant';

    try {
        const webpBuffer = await sharp(inputBuffer)
            .resize(512, 512, {
                fit: 'contain',
                background: { r: 0, g: 0, b: 0, alpha: 0 }
            })
            .webp({ quality: 80 })
            .toBuffer();

        return webpBuffer;
    } catch (err) {
        console.error('[StickerHelper] Gagal membuat stiker:', err.message);
        throw err;
    }
}

module.exports = {
    createSticker
};
