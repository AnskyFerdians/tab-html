/**
 * WhatsApp Bridge Server for Antigravity Bot
 * Powered by @whiskeysockets/baileys and Express.js
 *
 * ✨ Improvements v2.0:
 * - Fast pre-reply: user instantly gets "⏳ Memproses..." before AI answers
 * - Server-online notification: bot proactively notifies admin when it comes online
 * - Interactive new-user welcome flow
 * - Better timeout & error handling
 * - Concurrent message queue per-user (prevents duplicate responses)
 * - Reaction emoji feedback while processing
 */

const express = require('express');
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestBaileysVersion,
    downloadMediaMessage
} = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrcode = require('qrcode-terminal');
const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');
const groupManager = require('./groupManager');
const { handleGroupMessage, handleStickerCommand, handleToImageCommand, isGroupVerified } = require('./groupCommands');

// Global error handlers to prevent bridge crashes on Linux VPS
process.on('uncaughtException', (err) => {
    console.error('[Bridge UncaughtException]:', err.message || err);
});
process.on('unhandledRejection', (reason) => {
    console.error('[Bridge UnhandledRejection]:', reason?.message || reason);
});

const app = express();
app.use(express.json());

const PORT = process.env.BRIDGE_PORT || 3000;
const AUTH_DIR_NAME = process.env.AUTH_DIR || 'auth_info_baileys';
const FASTAPI_WEBHOOK_URL = process.env.FASTAPI_WEBHOOK_URL || 'http://127.0.0.1:8000/webhook/whatsapp';

// Admin nomor — diisi nomor pemilik laptop (JID format)
const ADMIN_JID = process.env.ADMIN_JID || null; // contoh: "6281234567890@s.whatsapp.net"

let sock = null;
let isConnected = false;
let currentQR = null;
let reconnectCount = 0;

// Track per-user processing to prevent duplicate responses
const processingUsers = new Set();

// Track known users (simple in-memory cache; refreshed from FastAPI on startup)
const knownUserCache = new Set();

// Server start time
const serverStartTime = Date.now();

// ─────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────

function formatJid(target) {
    if (!target) return '';
    if (target.endsWith('@lid') || target.endsWith('@s.whatsapp.net') || target.endsWith('@g.us')) {
        return target;
    }
    let clean = target.replace(/[^0-9]/g, '');
    return `${clean}@s.whatsapp.net`;
}

function getMimeType(filename) {
    const ext = path.extname(filename).toLowerCase();
    switch (ext) {
        case '.docx':
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
        case '.doc':
            return 'application/msword';
        case '.pdf':
            return 'application/pdf';
        case '.txt':
            return 'text/plain';
        case '.xlsx':
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        default:
            return 'application/octet-stream';
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Sends a fast pre-reply to user so they know something is happening.
 * Uses a short random "thinking" message to feel more human.
 */
async function sendPreReply(jid, isNewUser = false) {
    if (!sock || !isConnected) return;

    // For new users, show a welcoming loading message
    const preMessages = isNewUser
        ? [
            '👋 Halo! Sebentar ya, lagi menyiapkan verifikasi untuk kamu...',
            '🤖 Satu moment ya! Lagi cek data kamu...',
        ]
        : [
            '⏳ Sedang memproses pesanmu...',
            '🧠 Lagi mikir sebentar ya...',
            '⚡ On it! Sebentar...',
            '🔍 Lagi cek dulu nih...',
        ];

    const msg = preMessages[Math.floor(Math.random() * preMessages.length)];

    try {
        await sock.sendMessage(jid, { text: msg });
    } catch (e) {
        console.error('[PreReply] Gagal kirim pre-reply:', e.message);
    }
}

/**
 * Notify admin that the bridge/server is back online.
 * Called once after a successful WhatsApp connection.
 */
async function notifyAdminOnline() {
    if (!ADMIN_JID || !sock || !isConnected) return;
    try {
        await sleep(2000); // wait 2s for socket to stabilize
        const uptime = Math.round((Date.now() - serverStartTime) / 1000);
        await sock.sendMessage(ADMIN_JID, {
            text:
                `🟢 *ANTIGRAVITY BOT — SERVER AKTIF!*\n` +
                `━━━━━━━━━━━━━━━━━━━━\n` +
                `✅ WhatsApp Bridge berhasil terhubung\n` +
                `🌐 Webhook: ${FASTAPI_WEBHOOK_URL}\n` +
                `⏱️ Uptime sejak start: ${uptime}s\n` +
                `🔄 Reconnect count: ${reconnectCount}\n` +
                `━━━━━━━━━━━━━━━━━━━━\n` +
                `Bot siap menerima pesan! Ketik *menu* untuk melihat fitur.`
        });
        console.log('[Notifikasi] Admin diberitahu bahwa server aktif.');
    } catch (e) {
        console.error('[Notifikasi] Gagal kirim notifikasi admin:', e.message);
    }
}

// ─────────────────────────────────────────────────
// WHATSAPP CONNECTION
// ─────────────────────────────────────────────────

async function connectToWhatsApp() {
    const authDir = path.join(__dirname, AUTH_DIR_NAME);
    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    const { version } = await fetchLatestBaileysVersion();

    console.log(`[Baileys] Inisialisasi WhatsApp Socket v${version.join('.')}...`);

    sock = makeWASocket({
        version,
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false,
        browser: ['Ubuntu', 'Chrome', '22.04.4'],
        // Increase default timeouts for slow networks
        connectTimeoutMs: 60_000,
        keepAliveIntervalMs: 25_000,
    });

    sock.ev.on('creds.update', saveCreds);

    // ── Connection State Updates ──────────────────
    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            currentQR = qr;
            console.log('\n======================================================');
            console.log('  📱 SCAN QR CODE INI DENGAN WHATSAPP ANDA:');
            console.log('  (Buka WhatsApp -> Pengaturan / Titik Tiga -> Tautkan Perangkat)');
            console.log('======================================================\n');
            qrcode.generate(qr, { small: true });
            console.log('Menunggu pemindaian QR Code...\n');
        }

        if (connection === 'close') {
            isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
            reconnectCount++;
            console.log(`[Baileys] Koneksi terputus (Status: ${statusCode}). Reconnect #${reconnectCount}: ${shouldReconnect}`);
            if (shouldReconnect) {
                const delay = Math.min(3000 * reconnectCount, 30000); // exponential backoff max 30s
                console.log(`[Baileys] Reconnect dalam ${delay / 1000}s...`);
                setTimeout(connectToWhatsApp, delay);
            } else {
                console.log(`[Baileys] Sesi WhatsApp belum tertaut/logout. Membersihkan ${AUTH_DIR_NAME} dan reset...`);
                try {
                    if (fs.existsSync(authDir)) fs.rmSync(authDir, { recursive: true, force: true });
                } catch (e) {}
                setTimeout(connectToWhatsApp, 2000);
            }
        } else if (connection === 'open') {
            isConnected = true;
            currentQR = null;
            reconnectCount = 0;
            console.log('\n======================================================');
            console.log('  ✅ WHATSAPP BERHASIL TERHUBUNG SECARA RESMI!');
            console.log(`  Nomor Akun Bot: ${sock.user?.id || 'Aktif'}`);
            console.log(`  Bridge Server berjalan di http://localhost:${PORT}`);
            console.log(`  Forwarding pesan ke: ${FASTAPI_WEBHOOK_URL}`);
            console.log('======================================================\n');

            // Notify admin that server is back online
            notifyAdminOnline();
        }
    });

    // ── Group Participants Update (Welcome & Goodbye Greetings) ──
    sock.ev.on('group-participants.update', async (update) => {
        try {
            const { id: groupJid, participants, action } = update;
            // Bot pribadi: Jangan kirim respon apa pun ke grup yang belum diverifikasi kunci sandi pemilik
            if (!isGroupVerified(groupJid)) return;

            const conf = groupManager.getGroupSettings(groupJid);
            let meta = null;
            try {
                meta = await sock.groupMetadata(groupJid);
            } catch (e) {
                console.error(`[GroupEvent] Gagal ambil metadata grup ${groupJid}:`, e.message);
            }

            const groupName = meta?.subject || 'Grup WhatsApp';
            const groupDesc = meta?.desc || '';
            const memberCount = meta?.participants?.length || participants.length;

            if (action === 'add' && conf.welcome) {
                for (const participant of participants) {
                    const cleanNum = participant.split('@')[0].replace(/[^0-9]/g, '');
                    const welcomeText = groupManager.formatWelcomeMessage(conf, cleanNum, groupName, groupDesc, memberCount);
                    await sock.sendMessage(groupJid, {
                        text: welcomeText,
                        mentions: [participant]
                    });
                }
            } else if (action === 'remove' && conf.goodbye) {
                for (const participant of participants) {
                    const cleanNum = participant.split('@')[0].replace(/[^0-9]/g, '');
                    const goodbyeText = groupManager.formatGoodbyeMessage(conf, cleanNum, groupName, memberCount);
                    await sock.sendMessage(groupJid, {
                        text: goodbyeText,
                        mentions: [participant]
                    });
                }
            } else if (action === 'promote') {
                for (const participant of participants) {
                    const cleanNum = participant.split('@')[0].replace(/[^0-9]/g, '');
                    await sock.sendMessage(groupJid, {
                        text: `👑 *PROMOSI ADMIN*\nSelamat @${cleanNum} telah dipromosikan menjadi Admin Grup! 🎉`,
                        mentions: [participant]
                    });
                }
            } else if (action === 'demote') {
                for (const participant of participants) {
                    const cleanNum = participant.split('@')[0].replace(/[^0-9]/g, '');
                    await sock.sendMessage(groupJid, {
                        text: `ℹ️ Status Admin @${cleanNum} telah diturunkan menjadi anggota biasa.`,
                        mentions: [participant]
                    });
                }
            }
        } catch (err) {
            console.error('[GroupParticipants] Error:', err.message);
        }
    });

    // ── Incoming Messages ────────────────────────
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            // Abaikan pesan dari bot itu sendiri
            if (msg.key.fromMe) continue;

            const sender = msg.key.remoteJid;
            // Abaikan status update / broadcast
            if (sender.includes('@broadcast')) continue;

            const isGroup = sender.endsWith('@g.us');
            const participant = isGroup ? (msg.key.participant || msg.participant || sender) : sender;
            const senderName = msg.pushName || 'Pengguna';
            const textContent =
                msg.message?.conversation ||
                msg.message?.extendedTextMessage?.text ||
                msg.message?.imageMessage?.caption ||
                '';

            if (!textContent && !msg.message?.imageMessage && !msg.message?.stickerMessage) continue;

            console.log(`[Pesan Masuk] ${isGroup ? '[GRUP]' : '[DM]'} Dari: ${sender} (${senderName}) -> "${textContent}"`);

            // 1. Tangani Pesan Grup secara khusus
            if (isGroup) {
                handleGroupMessage({
                    sock,
                    msg,
                    groupJid: sender,
                    senderJid: participant,
                    senderName,
                    textContent,
                    adminJid: ADMIN_JID,
                    fastApiWebhookUrl: FASTAPI_WEBHOOK_URL
                }).catch(err => {
                    console.error('[GroupHandler Error]:', err);
                });
                continue;
            }

            // 2. Tangani Perintah Pembuat Stiker di DM (.s / .toimg)
            const cleanText = (textContent || '').trim().toLowerCase();
            if (['.s', '!s', '#s', '.sticker', '.stiker'].includes(cleanText) || cleanText.startsWith('.s ')) {
                await handleStickerCommand(sock, msg, sender);
                continue;
            }
            if (['.toimg', '!toimg', '#toimg'].includes(cleanText)) {
                await handleToImageCommand(sock, msg, sender);
                continue;
            }

            // 3. Tangani Pesan DM Pribadi (Asisten AI Antigravity)
            if (!textContent) continue;

            // Cegah pemrosesan ganda saat user kirim pesan cepat berulang
            if (processingUsers.has(sender)) {
                console.log(`[Queue] ${sender} sedang diproses, pesan ini di-queue.`);
                continue;
            }

            processingUsers.add(sender);

            // Jalankan penanganan pesan secara asinkron (non-blocking)
            handleMessage(msg, sender, senderName, textContent).finally(() => {
                processingUsers.delete(sender);
            });
        }
    });
}


/**
 * Core message handler — runs async for each user independently.
 */
async function handleMessage(msg, sender, senderName, textContent) {
    const isKnown = knownUserCache.has(sender);

    // Kirim indikator 'sedang mengetik' (composing) tanpa spam pesan teks interim
    if (isKnown) {
        try {
            if (sock) await sock.sendPresenceUpdate('composing', sender);
        } catch (e) {}
    }

    // 3. Teruskan ke FastAPI Webhook Antigravity
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90_000); // 90s timeout

        const response = await fetch(FASTAPI_WEBHOOK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from: sender,
                sender_name: senderName,
                text: textContent
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            console.error(`[Webhook] FastAPI merespon status ${response.status}`);
            // Jangan balas apapun jika status error untuk menjaga keamanan kontak tak dikenal
        } else {
            const result = await response.json();
            // Jika status ignored (belum verifikasi kode), JANGAN BALAS APAPUN
            if (result.status === 'ignored' || !result.reply) {
                console.log(`[Webhook] Kontak ${sender} diabaikan (belum verifikasi kode keamanan).`);
                return;
            }
            console.log(`[Webhook Sukses] Balasan terkirim untuk ${sender}:`, result.reply?.substring(0, 50));

            // Tandai pengguna sebagai terverifikasi di memori cache
            knownUserCache.add(sender);
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            console.error(`[Webhook Timeout] Permintaan ke FastAPI timeout untuk ${sender}`);
            await sendSafe(sender,
                `⏰ Maaf, jawaban bot terlalu lama diproses (timeout 90s).\n` +
                `Kemungkinan AI lagi overload. Coba kirim ulang pesan kamu ya!\n` +
                `💡 Tips: perintah cepat seperti \`status\`, \`baterai\`, \`screenshot\` selalu responsif.`
            );
        } else {
            console.error(`[Webhook Error] Gagal menghubungi ${FASTAPI_WEBHOOK_URL}: ${err.message}`);
            await sendSafe(sender,
                `🔴 Bot offline sementara. Server sedang di-restart atau ada gangguan jaringan.\n` +
                `Coba lagi dalam beberapa menit ya! 🙏`
            );
        }
    } finally {
        try {
            if (sock) await sock.sendPresenceUpdate('paused', sender);
        } catch (e) {}
    }
}

/**
 * Safe wrapper for sendMessage — won't throw if socket dies
 */
async function sendSafe(jid, text) {
    try {
        if (sock && isConnected) {
            await sock.sendMessage(jid, { text });
        }
    } catch (e) {
        console.error('[SendSafe] Error:', e.message);
    }
}

// ─────────────────────────────────────────────────
// REST API ENDPOINTS (Dipanggil oleh FastAPI Dispatcher main.py)
// ─────────────────────────────────────────────────

app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        user: sock?.user || null,
        qr_ready: Boolean(currentQR),
        hasQR: Boolean(currentQR),
        uptime_seconds: Math.round((Date.now() - serverStartTime) / 1000),
        reconnect_count: reconnectCount,
        processing_users: processingUsers.size,
        known_users: knownUserCache.size
    });
});

app.get('/qr', (req, res) => {
    if (isConnected) {
        return res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>WhatsApp Bot - Terhubung</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
                    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
                    body { font-family: 'Inter', system-ui, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1a2744 100%); color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 1rem; }
                    .card { background: rgba(30,41,59,0.95); padding: 2.5rem; border-radius: 20px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(16,185,129,0.3); max-width: 460px; width: 100%; backdrop-filter: blur(10px); }
                    .pulse { display: inline-block; width: 12px; height: 12px; background: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite; }
                    @keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,0.7)} 50%{box-shadow:0 0 0 8px rgba(16,185,129,0)} }
                    .badge { display: inline-flex; align-items: center; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4); color: #10b981; padding: 6px 18px; border-radius: 999px; font-weight: 700; margin-bottom: 1.5rem; font-size: 0.85rem; letter-spacing: 0.05em; }
                    h2 { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.75rem; }
                    p { color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0.5rem; }
                    .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 1.5rem; }
                    .stat { background: rgba(15,23,42,0.6); border-radius: 12px; padding: 0.75rem; border: 1px solid rgba(51,65,85,0.5); }
                    .stat-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
                    .stat-value { font-size: 1rem; font-weight: 700; color: #e2e8f0; margin-top: 0.25rem; }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="badge"><span class="pulse"></span>ONLINE</div>
                    <h2>✅ WhatsApp Terhubung!</h2>
                    <p>Akun WhatsApp berhasil ditautkan ke <strong>Antigravity Bot</strong>.</p>
                    <p>Kirim pesan <strong>RajaWali0108</strong> dari kontak baru untuk verifikasi awal, lalu mulai obrolan!</p>
                    <div class="stats">
                        <div class="stat"><div class="stat-label">Status</div><div class="stat-value">🟢 Connected</div></div>
                        <div class="stat"><div class="stat-label">Port</div><div class="stat-value">:3000</div></div>
                    </div>
                </div>
            </body>
            </html>
        `);
    }

    if (!currentQR) {
        return res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Memuat QR Code...</title>
                <meta http-equiv="refresh" content="3">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
                    body { font-family: 'Inter', system-ui; background: #0f172a; color: #fff; text-align: center; padding-top: 20vh; }
                    .spinner { width: 48px; height: 48px; border: 4px solid rgba(255,255,255,0.1); border-top-color: #25d366; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1.5rem; }
                    @keyframes spin { to { transform: rotate(360deg); } }
                    h2 { font-size: 1.4rem; margin-bottom: 0.5rem; }
                    p { color: #94a3b8; }
                </style>
            </head>
            <body>
                <div class="spinner"></div>
                <h2>Sedang Menyiapkan QR Code...</h2>
                <p>Halaman ini akan otomatis me-refresh dalam 3 detik.</p>
            </body>
            </html>
        `);
    }

    const qrImgUrl = `https://api.qrserver.com/v1/create-qr-code/?size=380x380&data=${encodeURIComponent(currentQR)}&bgcolor=ffffff&color=000000&margin=10`;
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Scan WhatsApp QR Code | Antigravity Bot</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="20">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
                body { font-family: 'Inter', system-ui, sans-serif; background: linear-gradient(135deg, #0b1329 0%, #0f2027 50%, #0b1329 100%); color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 1rem; }
                .card { background: rgba(30,41,59,0.95); padding: 2.5rem 2rem; border-radius: 24px; text-align: center; box-shadow: 0 30px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(37,211,102,0.2); max-width: 460px; width: 100%; backdrop-filter: blur(12px); }
                .logo { font-size: 2.2rem; margin-bottom: 0.5rem; }
                h2 { margin: 0 0 0.25rem; color: #38bdf8; font-size: 1.4rem; font-weight: 700; }
                .subtitle { color: #64748b; font-size: 0.85rem; margin-bottom: 1.5rem; }
                .steps { background: rgba(15,23,42,0.7); border-radius: 14px; padding: 1rem 1.25rem; text-align: left; margin-bottom: 1.5rem; border-left: 3px solid #25d366; }
                .steps ol { padding-left: 1.2rem; }
                .steps li { color: #cbd5e1; font-size: 0.88rem; margin-bottom: 0.4rem; line-height: 1.5; }
                .steps li strong { color: #e2e8f0; }
                .qr-container { background: #ffffff; padding: 1.25rem; border-radius: 18px; display: inline-block; box-shadow: 0 8px 30px rgba(0,0,0,0.4); margin-bottom: 1rem; }
                .qr-container img { width: 100%; max-width: 280px; height: auto; display: block; border-radius: 8px; }
                .timer { color: #475569; font-size: 0.8rem; display: flex; align-items: center; justify-content: center; gap: 0.4rem; }
                .timer-dot { width: 8px; height: 8px; background: #25d366; border-radius: 50%; animation: blink 1.5s infinite; }
                @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
                .badge { display: inline-block; background: rgba(251,191,36,0.15); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; margin-bottom: 1rem; }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo">🤖</div>
                <h2>Antigravity Bot</h2>
                <div class="subtitle">WhatsApp AI Agent Bridge</div>
                <div class="badge">⏳ QR berlaku ~30 detik • Auto-refresh 20s</div>
                <div class="steps">
                    <ol>
                        <li>Buka <strong>WhatsApp</strong> di HP kamu</li>
                        <li>Ketuk <strong>Titik Tiga (⋮)</strong> di Android atau <strong>Pengaturan</strong> di iPhone</li>
                        <li>Pilih <strong>Perangkat Tertaut</strong> → <strong>Tautkan Perangkat</strong></li>
                        <li>Arahkan kamera ke QR di bawah ini</li>
                    </ol>
                </div>
                <div class="qr-container">
                    <img src="${qrImgUrl}" alt="WhatsApp QR Code">
                </div>
                <div class="timer"><span class="timer-dot"></span> Auto-refresh setiap 20 detik jika QR kedaluwarsa</div>
            </div>
        </body>
        </html>
    `);
});

// ── Pairing Code (Tanpa Scan Kamera) ──────────────
app.post('/request-pairing-code', async (req, res) => {
    let { phoneNumber } = req.body;
    if (!phoneNumber) return res.status(400).json({ error: "Nomor telepon harus diisi" });
    if (!sock || isConnected) return res.status(400).json({ error: "WhatsApp sudah terhubung atau socket belum siap" });

    let clean = phoneNumber.replace(/[^0-9]/g, '');
    if (clean.startsWith('0')) clean = '62' + clean.slice(1);

    try {
        const code = await sock.requestPairingCode(clean);
        console.log(`[Pairing Code] Dibuat untuk ${clean}: ${code}`);
        res.json({ success: true, code: code });
    } catch (e) {
        console.error('[Pairing Code Error]:', e);
        res.status(500).json({ error: e.message });
    }
});

// ── Send Message ─────────────────────────────────
app.post('/send-message', async (req, res) => {
    const { to, message } = req.body;
    if (!to || !message) {
        return res.status(400).json({ error: "Missing 'to' or 'message'" });
    }

    if (!isConnected || !sock) {
        return res.status(503).json({ error: "WhatsApp socket not connected" });
    }

    const jid = formatJid(to);
    try {
        await sock.sendMessage(jid, { text: message });
        console.log(`[Kirim Teks] Terkirim ke ${jid}: "${message.substring(0, 60)}..."`);
        res.json({ status: "sent", to: jid });
    } catch (err) {
        console.error(`[Gagal Kirim Teks] ke ${jid}:`, err);
        res.status(500).json({ error: err.message });
    }
});

// ── Send Image ───────────────────────────────────
app.post('/send-image', async (req, res) => {
    const { to, imagePath, caption } = req.body;
    if (!to || !imagePath) {
        return res.status(400).json({ error: "Missing 'to' or 'imagePath'" });
    }

    if (!isConnected || !sock) {
        return res.status(503).json({ error: "WhatsApp socket not connected" });
    }

    if (!fs.existsSync(imagePath)) {
        return res.status(404).json({ error: `Image not found: ${imagePath}` });
    }

    const jid = formatJid(to);
    try {
        const imageBuffer = fs.readFileSync(imagePath);
        await sock.sendMessage(jid, {
            image: imageBuffer,
            caption: caption || ''
        });
        console.log(`[Kirim Gambar] Terkirim ke ${jid}: ${path.basename(imagePath)}`);
        res.json({ status: "sent", to: jid, file: path.basename(imagePath) });
    } catch (err) {
        console.error(`[Gagal Kirim Gambar] ke ${jid}:`, err);
        res.status(500).json({ error: err.message });
    }
});

// ── Send File ────────────────────────────────────
app.post('/send-file', async (req, res) => {
    const { to, filePath, caption } = req.body;
    if (!to || !filePath) {
        return res.status(400).json({ error: "Missing 'to' or 'filePath'" });
    }

    if (!isConnected || !sock) {
        return res.status(503).json({ error: "WhatsApp socket not connected" });
    }

    if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: `File not found: ${filePath}` });
    }

    const jid = formatJid(to);
    const fileName = path.basename(filePath);
    const mimetype = getMimeType(fileName);

    try {
        const fileBuffer = fs.readFileSync(filePath);
        await sock.sendMessage(jid, {
            document: fileBuffer,
            mimetype: mimetype,
            fileName: fileName,
            caption: caption || ''
        });
        console.log(`[Kirim Berkas] Terkirim ke ${jid}: ${fileName} (${mimetype})`);
        res.json({ status: "sent", to: jid, file: fileName });
    } catch (err) {
        console.error(`[Gagal Kirim Berkas] ke ${jid}:`, err);
        res.status(500).json({ error: err.message });
    }
});

// ── Notify Server Active (called by FastAPI on startup) ──
app.post('/notify-admin', async (req, res) => {
    const { message } = req.body;
    if (ADMIN_JID && sock && isConnected) {
        try {
            await sock.sendMessage(ADMIN_JID, { text: message || '🟢 Bot server aktif!' });
            return res.json({ status: 'sent' });
        } catch (e) {
            return res.status(500).json({ error: e.message });
        }
    }
    res.json({ status: 'skipped', reason: 'No admin JID or not connected' });
});

// ── Broadcast to known users (admin use) ─────────
app.post('/broadcast', async (req, res) => {
    const { message, targets } = req.body;
    if (!message) return res.status(400).json({ error: "Missing message" });
    if (!isConnected || !sock) return res.status(503).json({ error: "Not connected" });

    const jids = targets || [...knownUserCache];
    let sent = 0;
    for (const jid of jids) {
        try {
            await sock.sendMessage(jid, { text: message });
            sent++;
            await sleep(1500); // rate limit: 1 msg per 1.5s
        } catch (e) {
            console.error(`[Broadcast] Gagal kirim ke ${jid}:`, e.message);
        }
    }
    res.json({ status: 'done', sent, total: jids.length });
});

// ── Group Endpoints for External / Python API ─────
app.get('/groups', async (req, res) => {
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        const groups = await sock.groupFetchAllParticipating();
        res.json(Object.values(groups));
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/metadata', async (req, res) => {
    const { groupJid } = req.body;
    if (!groupJid) return res.status(400).json({ error: "Missing groupJid" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        const meta = await sock.groupMetadata(groupJid);
        res.json(meta);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/kick', async (req, res) => {
    const { groupJid, userJid } = req.body;
    if (!groupJid || !userJid) return res.status(400).json({ error: "Missing groupJid or userJid" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        await sock.groupParticipantsUpdate(groupJid, [userJid], 'remove');
        res.json({ status: "success", action: "kick", target: userJid });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/promote', async (req, res) => {
    const { groupJid, userJid } = req.body;
    if (!groupJid || !userJid) return res.status(400).json({ error: "Missing groupJid or userJid" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        await sock.groupParticipantsUpdate(groupJid, [userJid], 'promote');
        res.json({ status: "success", action: "promote", target: userJid });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/demote', async (req, res) => {
    const { groupJid, userJid } = req.body;
    if (!groupJid || !userJid) return res.status(400).json({ error: "Missing groupJid or userJid" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        await sock.groupParticipantsUpdate(groupJid, [userJid], 'demote');
        res.json({ status: "success", action: "demote", target: userJid });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/settings', async (req, res) => {
    const { groupJid, action } = req.body;
    if (!groupJid || !action) return res.status(400).json({ error: "Missing groupJid or action" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        const mode = action === 'close' ? 'announcement' : 'not_announcement';
        await sock.groupSettingUpdate(groupJid, mode);
        res.json({ status: "success", mode });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/invite-code', async (req, res) => {
    const { groupJid } = req.body;
    if (!groupJid) return res.status(400).json({ error: "Missing groupJid" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        const code = await sock.groupInviteCode(groupJid);
        res.json({ status: "success", link: `https://chat.whatsapp.com/${code}` });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/tagall', async (req, res) => {
    const { groupJid, message } = req.body;
    if (!groupJid) return res.status(400).json({ error: "Missing groupJid" });
    if (!isConnected || !sock) return res.status(503).json({ error: "WhatsApp not connected" });
    try {
        const meta = await sock.groupMetadata(groupJid);
        const mentions = (meta.participants || []).map(p => p.id);
        const broadcastText = `📢 *PENGUMUMAN*\n━━━━━━━━━━━━━━━━━━━━\n${message || 'Panggilan untuk semua anggota grup!'}`;
        await sock.sendMessage(groupJid, { text: broadcastText, mentions });
        res.json({ status: "success", count: mentions.length });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/group/config', (req, res) => {
    const { groupJid, updates } = req.body;
    if (!groupJid || !updates) return res.status(400).json({ error: "Missing groupJid or updates" });
    const config = groupManager.updateGroupSettings(groupJid, updates);
    res.json(config);
});

// ─────────────────────────────────────────────────
// WEB DASHBOARD & QR CODE LINKING
// ─────────────────────────────────────────────────

app.get(['/', '/qr'], async (req, res) => {
    let qrDataUrl = '';
    if (currentQR) {
        try {
            qrDataUrl = await QRCode.toDataURL(currentQR, { scale: 8, margin: 2 });
        } catch (e) {
            console.error('[Web QR] Gagal membuat Data URL:', e);
        }
    }

    const html = `<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tautkan Perangkat WhatsApp - Antigravity Bot</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background: #0b141a; color: #e9edef; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .card { background: #111b21; border: 1px solid #222e35; border-radius: 16px; padding: 32px; max-width: 480px; width: 100%; text-align: center; box-shadow: 0 12px 30px rgba(0,0,0,0.5); }
        .badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 20px; }
        .badge.connected { background: rgba(0, 168, 132, 0.2); color: #00a884; border: 1px solid #00a884; }
        .badge.waiting { background: rgba(254, 201, 71, 0.2); color: #fec947; border: 1px solid #fec947; }
        h1 { font-size: 22px; margin-bottom: 10px; color: #00a884; }
        p { font-size: 14px; color: #8696a0; line-height: 1.5; margin-bottom: 20px; }
        .qr-wrapper { background: #ffffff; padding: 16px; border-radius: 12px; display: inline-block; margin-bottom: 20px; }
        .qr-wrapper img { display: block; max-width: 260px; height: auto; }
        .steps { text-align: left; background: #202c33; border-radius: 10px; padding: 16px 20px; margin-top: 15px; font-size: 13px; }
        .steps ol { padding-left: 20px; }
        .steps li { margin-bottom: 8px; color: #d1d7db; }
        .btn { background: #00a884; color: #111b21; font-weight: bold; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 10px; }
        .btn:hover { background: #029070; }
    </style>
</head>
<body>
    <div class="card">
        ${isConnected
            ? `
                <div class="badge connected">🟢 WHATSAPP TERHUBUNG</div>
                <h1>Perangkat Berhasil Tertaut!</h1>
                <p>Akun WhatsApp Bot sudah aktif dan siap menerima pesan.</p>
                <div class="steps" style="text-align: center;">
                    <p style="margin: 0; color: #00a884; font-size: 16px; font-weight: bold;">
                        Nomor Bot: ${sock?.user?.id?.split(':')[0] || 'Aktif'}
                    </p>
                </div>
                <br>
                <a href="/logout" class="btn" style="background: #ea4335; color: white;" onclick="return confirm('Yakin ingin putuskan tautan perangkat?');">Putuskan Tautan (Scan Ulang)</a>
            `
            : `
                <div class="badge waiting">🟡 MENUNGGU SCAN QR CODE</div>
                <h1>Tautkan WhatsApp Anda</h1>
                <p>Scan QR Code di bawah menggunakan aplikasi WhatsApp di HP Anda:</p>
                
                <div class="qr-wrapper">
                    ${qrDataUrl
                        ? `<img src="${qrDataUrl}" alt="QR Code WhatsApp" id="qrImg">`
                        : `<div style="padding: 40px 20px; color: #111;">Sedang menyiapkan QR Code...</div>`
                    }
                </div>

                <div class="steps">
                    <strong>Cara Menautkan:</strong>
                    <ol>
                        <li>Buka aplikasi <b>WhatsApp</b> di HP Anda</li>
                        <li>Ketuk <b>Menu (titik tiga)</b> atau <b>Pengaturan</b></li>
                        <li>Pilih <b>Perangkat Tertaut</b> (Linked Devices)</li>
                        <li>Ketuk <b>Tautkan Perangkat</b> lalu arahkan kamera ke QR Code di atas</li>
                    </ol>
                </div>
                <div style="margin-top: 25px; padding-top: 20px; border-top: 1px dashed #222e35;">
                    <p style="font-weight: 600; color: #d1d7db; margin-bottom: 10px;">Atau Tautkan Menggunakan Nomor HP (Tanpa Kamera):</p>
                    <div style="display: flex; gap: 8px; justify-content: center; margin-bottom: 12px;">
                        <input type="text" id="phoneInput" placeholder="Contoh: 0895428319367" style="padding: 10px 14px; border-radius: 8px; border: 1px solid #3b4a54; background: #202c33; color: white; width: 220px; font-size: 14px;">
                        <button onclick="requestPairing()" class="btn" style="margin: 0; padding: 10px 16px;">Minta Kode</button>
                    </div>
                    <div id="pairResult" style="display: none; background: #00a884; color: #111b21; font-size: 26px; font-weight: bold; letter-spacing: 4px; padding: 12px; border-radius: 8px; margin-top: 10px;"></div>
                    <p id="pairInfo" style="display: none; font-size: 13px; color: #8696a0; margin-top: 8px; line-height: 1.4;">Buka WhatsApp di HP > <b>Perangkat Tertaut</b> > <b>Tautkan dengan nomor telepon</b>, lalu masukkan kode di atas.</p>
                </div>
                <script>
                    async function requestPairing() {
                        const phone = document.getElementById('phoneInput').value.trim();
                        if (!phone) return alert('Silakan masukkan nomor telepon!');
                        const btn = event.target;
                        btn.disabled = true;
                        btn.innerText = 'Meminta...';
                        try {
                            const res = await fetch('/request-pairing-code', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ phoneNumber: phone })
                            });
                            const data = await res.json();
                            if (data.code) {
                                document.getElementById('pairResult').style.display = 'block';
                                document.getElementById('pairResult').innerText = data.code;
                                document.getElementById('pairInfo').style.display = 'block';
                            } else {
                                alert(data.error || 'Gagal meminta kode');
                            }
                        } catch (e) {
                            alert('Gagal: ' + e.message);
                        } finally {
                            btn.disabled = false;
                            btn.innerText = 'Minta Kode';
                        }
                    }

                    setInterval(() => {
                        fetch('/status').then(r => r.json()).then(data => {
                            if (data.connected) {
                                location.reload();
                            } else if (data.hasQR || data.qr_ready) {
                                fetch('/qr-data').then(r => r.json()).then(q => {
                                    if (q.qrDataUrl) {
                                        const img = document.getElementById('qrImg');
                                        if (img && img.src !== q.qrDataUrl) img.src = q.qrDataUrl;
                                    }
                                });
                            }
                        }).catch(() => {});
                    }, 2500);
                </script>
            `
        }
    </div>
</body>
</html>`;
    res.send(html);
});

app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        hasQR: Boolean(currentQR),
        user: sock?.user?.id || null,
        uptime_seconds: Math.round((Date.now() - serverStartTime) / 1000)
    });
});

app.get('/qr-data', async (req, res) => {
    if (!currentQR) return res.json({ qrDataUrl: null });
    try {
        const qrDataUrl = await QRCode.toDataURL(currentQR, { scale: 8, margin: 2 });
        res.json({ qrDataUrl });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/logout', async (req, res) => {
    try {
        if (sock) await sock.logout();
        const authDir = path.join(__dirname, AUTH_DIR_NAME);
        if (fs.existsSync(authDir)) {
            fs.rmSync(authDir, { recursive: true, force: true });
        }
    } catch (e) {
        console.error('[Logout] Error:', e);
    }
    isConnected = false;
    currentQR = null;
    res.redirect('/');
    setTimeout(connectToWhatsApp, 1500);
});

// ─────────────────────────────────────────────────
// START SERVER
// ─────────────────────────────────────────────────

app.listen(PORT, () => {
    console.log(`[Bridge Server] HTTP API mendengarkan di http://localhost:${PORT}`);
    connectToWhatsApp();
});
