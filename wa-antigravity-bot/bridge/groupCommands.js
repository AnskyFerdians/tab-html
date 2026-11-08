/**
 * Group Commands & Protection Handler for WhatsApp Antigravity Bot
 * Implements:
 * - Anti-Link detection & auto-kick / warning
 * - Welcome & Goodbye Greetings
 * - Kick / Promote / Demote
 * - TagAll / HideTag
 * - Group Open / Close
 * - Group Link & Info
 * - Sticker Maker (.s) & ToImage (.toimg)
 * - AI integration in group (.ai / @bot)
 */

const { downloadMediaMessage } = require('@whiskeysockets/baileys');
const pino = require('pino');
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const groupManager = require('./groupManager');
const { createSticker } = require('./stickerHelper');

const VERIFIED_STORAGE = path.join(__dirname, '..', 'storage', 'verified_users.json');

function isGroupVerified(gid) {
    try {
        if (!fs.existsSync(VERIFIED_STORAGE)) return false;
        const raw = fs.readFileSync(VERIFIED_STORAGE, 'utf-8');
        const data = JSON.parse(raw);
        const users = data.verified_users || [];
        const cleanGid = gid.split('@')[0];
        return users.includes(gid) || users.includes(cleanGid);
    } catch (e) {
        return false;
    }
}

function markGroupVerified(gid) {
    try {
        let data = { verified_users: [] };
        if (fs.existsSync(VERIFIED_STORAGE)) {
            data = JSON.parse(fs.readFileSync(VERIFIED_STORAGE, 'utf-8'));
        }
        if (!data.verified_users) data.verified_users = [];
        const cleanGid = gid.split('@')[0];
        if (!data.verified_users.includes(gid)) data.verified_users.push(gid);
        if (!data.verified_users.includes(cleanGid)) data.verified_users.push(cleanGid);
        fs.writeFileSync(VERIFIED_STORAGE, JSON.stringify(data, null, 2), 'utf-8');
    } catch (e) {
        console.error('[GroupHandler] Error saving group verification:', e);
    }
}

/**
 * Handle incoming message from a WhatsApp Group
 */
async function handleGroupMessage({
    sock,
    msg,
    groupJid,
    senderJid,
    senderName,
    textContent,
    adminJid,
    fastApiWebhookUrl
}) {
    // 0. CEK VERIFIKASI KODE KEAMANAN UNTUK GRUP
    const textClean = (textContent || '').trim().toLowerCase();
    const hasSecurityCode = textClean.includes('rajawali0108');

    if (hasSecurityCode) {
        markGroupVerified(groupJid);
        await sock.sendMessage(groupJid, {
            text: '🛡️ *Grup Berhasil Diaktifkan!*\n' +
                  '━━━━━━━━━━━━━━━━━━━━\n' +
                  '✅ Kode keamanan valid! Bot sekarang resmi aktif di grup ini.\n' +
                  'Gunakan `.ai [pertanyaan]` atau tag saya untuk mulai berinteraksi.'
        }, { quoted: msg });
        return;
    }

    // Jika grup BELUM diverifikasi dengan kode keamanan:
    // ATURAN TEGAS PENGGUNA: JANGAN DIBALAS SAMA SEKALI (Silent ignore)!
    if (!isGroupVerified(groupJid)) {
        return;
    }

    // 1. Dapatkan metadata grup untuk memeriksa status admin
    let groupMetadata = null;
    try {
        groupMetadata = await sock.groupMetadata(groupJid);
    } catch (e) {
        console.error(`[GroupHandler] Gagal mengambil metadata grup ${groupJid}:`, e.message);
    }

    const botJid = sock.user?.id ? sock.user.id.split(':')[0] + '@s.whatsapp.net' : '';
    const isSenderAdmin = groupManager.isUserAdmin(groupMetadata, senderJid);
    const isBotAdmin = groupManager.isBotAdmin(groupMetadata, botJid);
    const isOwner = adminJid && senderJid.includes(adminJid.replace(/[^0-9]/g, ''));

    // ─────────────────────────────────────────────────────────────
    // 2. SISTEM PROTEKSI ANTI-LINK (AUTO-DETECT & ENFORCE)
    // ─────────────────────────────────────────────────────────────
    const conf = groupManager.getGroupSettings(groupJid);

    if (groupManager.containsLink(textContent)) {
        // Jika pengirim bukan Admin/Owner dan Anti-Link aktif di grup ini
        if (!isSenderAdmin && !isOwner && conf.antilink) {
            console.log(`[Anti-Link] Link terdeteksi dari non-admin ${senderJid} di grup ${groupJid}`);

            // A. Hapus pesan yang melanggar sesegera mungkin
            try {
                await sock.sendMessage(groupJid, { delete: msg.key });
            } catch (err) {
                console.error('[Anti-Link] Gagal menghapus pesan:', err.message);
            }

            const userCleanNum = senderJid.split('@')[0].replace(/[^0-9]/g, '');

            // B. Eksekusi tindakan berdasarkan konfigurasi (kick / warn / delete)
            if (conf.antilink_action === 'kick') {
                if (isBotAdmin) {
                    try {
                        await sock.groupParticipantsUpdate(groupJid, [senderJid], 'remove');
                        await sock.sendMessage(groupJid, {
                            text: `⛔ *ANTI-LINK KICK*\n\nMaaf @${userCleanNum}, Anda dikeluarkan dari grup karena dilarang membagikan tautan/link di sini!`,
                            mentions: [senderJid]
                        });
                    } catch (e) {
                        console.error('[Anti-Link] Gagal kick user:', e.message);
                    }
                } else {
                    await sock.sendMessage(groupJid, {
                        text: `⚠️ *ANTI-LINK DETECTED*\n\nPesan dari @${userCleanNum} dihapus karena berisi tautan. (Bot belum menjadi Admin untuk melakukan kick otomatis).`,
                        mentions: [senderJid]
                    });
                }
            } else {
                // Mode Peringatan (Warn: 3x peringatan = Kick)
                const warns = groupManager.addWarning(groupJid, senderJid);
                if (warns >= 3) {
                    if (isBotAdmin) {
                        try {
                            await sock.groupParticipantsUpdate(groupJid, [senderJid], 'remove');
                            groupManager.resetWarnings(groupJid, senderJid);
                            await sock.sendMessage(groupJid, {
                                text: `⛔ *ANTI-LINK AUTO-KICK*\n\n@${userCleanNum} telah dikeluarkan dari grup karena mencapai batas maksimal *3x peringatan* tautan!`,
                                mentions: [senderJid]
                            });
                        } catch (e) {
                            console.error('[Anti-Link] Gagal auto-kick 3x warn:', e.message);
                        }
                    } else {
                        await sock.sendMessage(groupJid, {
                            text: `⚠️ *PERINGATAN MAKSIMAL (3/3)*\n\n@${userCleanNum} telah melanggar aturan tautan 3 kali! Harap admin menindak peserta ini.`,
                            mentions: [senderJid]
                        });
                    }
                } else {
                    await sock.sendMessage(groupJid, {
                        text: `⚠️ *PERINGATAN ANTI-LINK (${warns}/3)*\n━━━━━━━━━━━━━━━━━━━━\nHalo @${userCleanNum}, dilarang mengirimkan tautan di grup ini!\nPesan kamu telah dihapus oleh sistem keamanan.\n_Jika mencapai 3 kali peringatan, kamu akan otomatis dikeluarkan._`,
                        mentions: [senderJid]
                    });
                }
            }
            return; // Hentikan pemrosesan pesan lebih lanjut
        }
    }

    // ─────────────────────────────────────────────────────────────
    // 3. PARSING PERINTAH (COMMAND DISPATCHER)
    // ─────────────────────────────────────────────────────────────
    const trimmed = textContent.trim();
    // Support prefix ., !, #, /, atau langsung teks perintah
    const prefixRegex = /^[.!#/]/;
    const hasPrefix = prefixRegex.test(trimmed);
    const cleanCmdText = hasPrefix ? trimmed.slice(1).trim() : trimmed;
    const parts = cleanCmdText.split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);
    const fullArgs = args.join(' ').trim();

    // Mentioned target helper
    function getTargetJid() {
        // Dari mention
        const contextInfo = msg.message?.extendedTextMessage?.contextInfo;
        if (contextInfo?.mentionedJid && contextInfo.mentionedJid.length > 0) {
            return contextInfo.mentionedJid[0];
        }
        // Dari reply/quoted message
        if (contextInfo?.participant) {
            return contextInfo.participant;
        }
        // Dari argumen teks nomor HP
        if (args[0]) {
            const clean = args[0].replace(/[^0-9]/g, '');
            if (clean.length >= 8) {
                return `${clean}@s.whatsapp.net`;
            }
        }
        return null;
    }

    // ── Command: MENU / BANTUAN ──────────────────────────────────
    if (['menu', 'help', 'bantuan', 'fitur'].includes(command) && (hasPrefix || parts.length === 1)) {
        const menuText =
            `╭━━━━━━━━━━━━━━━━━━━━━━━━╮\n` +
            `┃   🛡️ *ANTIGRAVITY BOT PRO*   ┃\n` +
            `┃      _Group & AI Manager_      ┃\n` +
            `╰━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n` +
            `👥 *Nama Grup:* ${groupMetadata?.subject || 'WhatsApp Group'}\n` +
            `👑 *Status Anda:* ${isSenderAdmin ? '⭐ Admin' : '👤 Anggota'}\n` +
            `🤖 *Status Bot:* ${isBotAdmin ? '✅ Admin (Aktif)' : '⚠️ Bukan Admin'}\n\n` +
            `┌── 🛡️ *PROTEKSI & ADMIN GRUP* ──┐\n` +
            `│ • *.antilink [on|off|kick|warn]*\n` +
            `│ • *.welcome [on|off]*\n` +
            `│ • *.goodbye [on|off]*\n` +
            `│ • *.setwelcome [teks sambutan]*\n` +
            `│ • *.setgoodbye [teks perpisahan]*\n` +
            `│ • *.kick @user* (Keluarkan member)\n` +
            `│ • *.promote @user* (Naikkan admin)\n` +
            `│ • *.demote @user* (Turunkan admin)\n` +
            `│ • *.tagall [pesan]* (Panggil semua)\n` +
            `│ • *.hidetag [pesan]* (Tag tak terlihat)\n` +
            `│ • *.tutupgrup* (Hanya admin yg chat)\n` +
            `│ • *.bukagrup* (Buka chat semua)\n` +
            `│ • *.linkgrup* (Ambil link undangan)\n` +
            `│ • *.infogrup* (Detail profil grup)\n` +
            `└── ━━━━━━━━━━━━━━━━━━━━━━ ──┘\n\n` +
            `┌── 🎨 *MEDIA & STIKER* ──┐\n` +
            `│ • *.s / .sticker* (Balas/kirim gambar)\n` +
            `│ • *.toimg* (Balas stiker jadi gambar)\n` +
            `└── ━━━━━━━━━━━━━━━━━━━━━━ ──┘\n\n` +
            `┌── 🧠 *KECERDASAN BUATAN (AI)* ──┐\n` +
            `│ • *.ai [pertanyaan]* (Tanya Gemini AI)\n` +
            `│ • Atau *tag @bot* dengan pertanyaan\n` +
            `└── ━━━━━━━━━━━━━━━━━━━━━━ ──┘\n\n` +
            `📌 _Gunakan tanda titik (.) di awal perintah._`;

        await sock.sendMessage(groupJid, { text: menuText }, { quoted: msg });
        return;
    }

    // ── Command: STIKER MAKER (.s / .sticker) ────────────────────
    if (['s', 'sticker', 'stiker'].includes(command)) {
        await handleStickerCommand(sock, msg, groupJid);
        return;
    }

    // ── Command: TO IMAGE (.toimg) ──────────────────────────────
    if (['toimg', 'toimage'].includes(command)) {
        await handleToImageCommand(sock, msg, groupJid);
        return;
    }

    // ── Command: KICK MEMBER ─────────────────────────────────────
    if (['kick', 'tendang', 'keluarkan'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Perintah ini khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!isBotAdmin) {
            await sock.sendMessage(groupJid, { text: '⚠️ Bot harus dijadikan *Admin Grup* terlebih dahulu untuk mengeluarkan anggota!' }, { quoted: msg });
            return;
        }

        const target = getTargetJid();
        if (!target) {
            await sock.sendMessage(groupJid, { text: '⚠️ Tag atau balas pesan anggota yang ingin dikeluarkan!\nContoh: `.kick @user`' }, { quoted: msg });
            return;
        }

        if (target === botJid) {
            await sock.sendMessage(groupJid, { text: '😅 Saya tidak bisa mengeluarkan diri saya sendiri!' }, { quoted: msg });
            return;
        }

        try {
            await sock.groupParticipantsUpdate(groupJid, [target], 'remove');
            const targetClean = target.split('@')[0].replace(/[^0-9]/g, '');
            await sock.sendMessage(groupJid, {
                text: `✅ Berhasil mengeluarkan @${targetClean} dari grup oleh admin @${senderJid.split('@')[0]}.`,
                mentions: [target, senderJid]
            });
        } catch (e) {
            await sock.sendMessage(groupJid, { text: `❌ Gagal mengeluarkan anggota: ${e.message}` }, { quoted: msg });
        }
        return;
    }

    // ── Command: PROMOTE ADMIN ───────────────────────────────────
    if (['promote', 'jadikanadmin'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Perintah ini khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!isBotAdmin) {
            await sock.sendMessage(groupJid, { text: '⚠️ Bot harus dijadikan *Admin Grup* terlebih dahulu untuk mempromosikan admin!' }, { quoted: msg });
            return;
        }

        const target = getTargetJid();
        if (!target) {
            await sock.sendMessage(groupJid, { text: '⚠️ Tag atau balas pesan anggota yang ingin dinaikkan jadi Admin!\nContoh: `.promote @user`' }, { quoted: msg });
            return;
        }

        try {
            await sock.groupParticipantsUpdate(groupJid, [target], 'promote');
            const targetClean = target.split('@')[0].replace(/[^0-9]/g, '');
            await sock.sendMessage(groupJid, {
                text: `👑 *PROMOSI ADMIN*\n\nSelamat @${targetClean}, Anda telah diangkat menjadi Admin Grup oleh @${senderJid.split('@')[0]}! 🎉`,
                mentions: [target, senderJid]
            });
        } catch (e) {
            await sock.sendMessage(groupJid, { text: `❌ Gagal menaikkan admin: ${e.message}` }, { quoted: msg });
        }
        return;
    }

    // ── Command: DEMOTE ADMIN ────────────────────────────────────
    if (['demote', 'turunkanadmin'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Perintah ini khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!isBotAdmin) {
            await sock.sendMessage(groupJid, { text: '⚠️ Bot harus dijadikan *Admin Grup* terlebih dahulu!' }, { quoted: msg });
            return;
        }

        const target = getTargetJid();
        if (!target) {
            await sock.sendMessage(groupJid, { text: '⚠️ Tag atau balas pesan admin yang ingin diturunkan jabatannya!\nContoh: `.demote @user`' }, { quoted: msg });
            return;
        }

        try {
            await sock.groupParticipantsUpdate(groupJid, [target], 'demote');
            const targetClean = target.split('@')[0].replace(/[^0-9]/g, '');
            await sock.sendMessage(groupJid, {
                text: `ℹ️ Status Admin @${targetClean} telah diturunkan menjadi anggota biasa oleh @${senderJid.split('@')[0]}.`,
                mentions: [target, senderJid]
            });
        } catch (e) {
            await sock.sendMessage(groupJid, { text: `❌ Gagal menurunkan status admin: ${e.message}` }, { quoted: msg });
        }
        return;
    }

    // ── Command: TAGALL / HIDETAG ────────────────────────────────
    if (['tagall', 'hidetag', 'everyone'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Fitur panggilan massal khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }

        const participants = groupMetadata?.participants || [];
        const mentions = participants.map(p => p.id);
        const broadcastMsg = fullArgs || 'Panggilan pengumuman penting untuk semua anggota grup!';

        let tagText = `📢 *PENGUMUMAN GRUP*\n`;
        tagText += `━━━━━━━━━━━━━━━━━━━━\n`;
        tagText += `💬 *Pesan:* ${broadcastMsg}\n`;
        tagText += `👑 *Oleh:* @${senderJid.split('@')[0]}\n`;
        tagText += `━━━━━━━━━━━━━━━━━━━━\n\n`;

        if (command === 'tagall') {
            tagText += `👥 *Daftar Anggota (${participants.length}):*\n`;
            for (let i = 0; i < participants.length; i++) {
                const num = participants[i].id.split('@')[0].replace(/[^0-9]/g, '');
                tagText += `${i + 1}. @${num}\n`;
            }
        }

        await sock.sendMessage(groupJid, { text: tagText, mentions });
        return;
    }

    // ── Command: ANTI-LINK CONFIG ────────────────────────────────
    if (['antilink', 'proteksilink'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Perintah ini khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }

        const sub = args[0]?.toLowerCase();
        if (sub === 'on' || sub === 'aktif') {
            groupManager.updateGroupSettings(groupJid, { antilink: true });
            await sock.sendMessage(groupJid, { text: '✅ *Anti-Link DIAKTIFKAN!*\nPesan berisi link dari non-admin akan otomatis dihapus.' }, { quoted: msg });
        } else if (sub === 'off' || sub === 'nonaktif') {
            groupManager.updateGroupSettings(groupJid, { antilink: false });
            await sock.sendMessage(groupJid, { text: '⚪ *Anti-Link DINONAKTIFKAN!*\nAnggota bebas membagikan link.' }, { quoted: msg });
        } else if (sub === 'kick') {
            groupManager.updateGroupSettings(groupJid, { antilink: true, antilink_action: 'kick' });
            await sock.sendMessage(groupJid, { text: '🚨 *Anti-Link Mode KICK Aktif!*\nNon-admin yang kirim link akan LANGSUNG dikeluarkan.' }, { quoted: msg });
        } else if (sub === 'warn') {
            groupManager.updateGroupSettings(groupJid, { antilink: true, antilink_action: 'warn' });
            await sock.sendMessage(groupJid, { text: '⚠️ *Anti-Link Mode PERINGATAN Aktif!*\nNon-admin yang kirim link diberi 3x peringatan sebelum dikeluarkan.' }, { quoted: msg });
        } else {
            const cur = groupManager.getGroupSettings(groupJid);
            await sock.sendMessage(groupJid, {
                text:
                    `⚙️ *STATUS PENGATURAN ANTI-LINK*\n` +
                    `━━━━━━━━━━━━━━━━━━━━\n` +
                    `• Status: *${cur.antilink ? '🟢 AKTIF' : '⚪ NONAKTIF'}*\n` +
                    `• Tindakan: *${cur.antilink_action.toUpperCase()}*\n\n` +
                    `*Cara Mengubah:*\n` +
                    `• \`.antilink on\` (Aktifkan)\n` +
                    `• \`.antilink off\` (Nonaktifkan)\n` +
                    `• \`.antilink warn\` (Hapus & 3x peringatan kick)\n` +
                    `• \`.antilink kick\` (Langsung kick)`
            }, { quoted: msg });
        }
        return;
    }

    // ── Command: WELCOME & GOODBYE CONFIG ────────────────────────
    if (['welcome', 'sambutan'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Perintah ini khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        const sub = args[0]?.toLowerCase();
        if (sub === 'on' || sub === 'aktif') {
            groupManager.updateGroupSettings(groupJid, { welcome: true });
            await sock.sendMessage(groupJid, { text: '✅ *Pesan Sambutan (Welcome) DIAKTIFKAN!*' }, { quoted: msg });
        } else if (sub === 'off' || sub === 'nonaktif') {
            groupManager.updateGroupSettings(groupJid, { welcome: false });
            await sock.sendMessage(groupJid, { text: '⚪ *Pesan Sambutan (Welcome) DINONAKTIFKAN!*' }, { quoted: msg });
        } else {
            await sock.sendMessage(groupJid, {
                text: `Ketik \`.welcome on\` untuk mengaktifkan atau \`.welcome off\` untuk menonaktifkan.`
            }, { quoted: msg });
        }
        return;
    }

    if (['goodbye', 'perpisahan'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Perintah ini khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        const sub = args[0]?.toLowerCase();
        if (sub === 'on' || sub === 'aktif') {
            groupManager.updateGroupSettings(groupJid, { goodbye: true });
            await sock.sendMessage(groupJid, { text: '✅ *Pesan Perpisahan (Goodbye) DIAKTIFKAN!*' }, { quoted: msg });
        } else if (sub === 'off' || sub === 'nonaktif') {
            groupManager.updateGroupSettings(groupJid, { goodbye: false });
            await sock.sendMessage(groupJid, { text: '⚪ *Pesan Perpisahan (Goodbye) DINONAKTIFKAN!*' }, { quoted: msg });
        } else {
            await sock.sendMessage(groupJid, {
                text: `Ketik \`.goodbye on\` untuk mengaktifkan atau \`.goodbye off\` untuk menonaktifkan.`
            }, { quoted: msg });
        }
        return;
    }

    if (['setwelcome'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!fullArgs) {
            await sock.sendMessage(groupJid, {
                text: `Format: \`.setwelcome [pesan sambutan]\`\n\nVariabel yang bisa dipakai:\n• {user} = tag pengguna\n• {group} = nama grup\n• {members} = jumlah anggota\n• {desc} = deskripsi grup`
            }, { quoted: msg });
            return;
        }
        groupManager.updateGroupSettings(groupJid, { custom_welcome: fullArgs });
        await sock.sendMessage(groupJid, { text: '✅ Pesan sambutan kustom berhasil disimpan!' }, { quoted: msg });
        return;
    }

    if (['setgoodbye'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!fullArgs) {
            await sock.sendMessage(groupJid, {
                text: `Format: \`.setgoodbye [pesan perpisahan]\`\n\nVariabel yang bisa dipakai:\n• {user} = tag pengguna\n• {group} = nama grup\n• {members} = jumlah anggota`
            }, { quoted: msg });
            return;
        }
        groupManager.updateGroupSettings(groupJid, { custom_goodbye: fullArgs });
        await sock.sendMessage(groupJid, { text: '✅ Pesan perpisahan kustom berhasil disimpan!' }, { quoted: msg });
        return;
    }

    // ── Command: BUKA / TUTUP GRUP ───────────────────────────────
    if (['tutupgrup', 'closegroup', 'mute'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!isBotAdmin) {
            await sock.sendMessage(groupJid, { text: '⚠️ Bot harus menjadi Admin grup terlebih dahulu!' }, { quoted: msg });
            return;
        }
        try {
            await sock.groupSettingUpdate(groupJid, 'announcement');
            await sock.sendMessage(groupJid, {
                text: '🔒 *GRUP DITUTUP*\nSekarang hanya Admin yang dapat mengirim pesan ke grup ini.'
            });
        } catch (e) {
            await sock.sendMessage(groupJid, { text: `❌ Gagal menutup grup: ${e.message}` }, { quoted: msg });
        }
        return;
    }

    if (['bukagrup', 'opengroup', 'unmute'].includes(command)) {
        if (!isSenderAdmin && !isOwner) {
            await sock.sendMessage(groupJid, { text: '⛔ Khusus untuk *Admin Grup*!' }, { quoted: msg });
            return;
        }
        if (!isBotAdmin) {
            await sock.sendMessage(groupJid, { text: '⚠️ Bot harus menjadi Admin grup terlebih dahulu!' }, { quoted: msg });
            return;
        }
        try {
            await sock.groupSettingUpdate(groupJid, 'not_announcement');
            await sock.sendMessage(groupJid, {
                text: '🔓 *GRUP DIBUKA*\nSekarang semua anggota dapat mengirim pesan ke grup ini kembali.'
            });
        } catch (e) {
            await sock.sendMessage(groupJid, { text: `❌ Gagal membuka grup: ${e.message}` }, { quoted: msg });
        }
        return;
    }

    // ── Command: LINK GRUP ───────────────────────────────────────
    if (['linkgrup', 'linkgroup', 'invitelink'].includes(command)) {
        if (!isBotAdmin) {
            await sock.sendMessage(groupJid, { text: '⚠️ Bot harus menjadi Admin grup untuk mengambil link undangan!' }, { quoted: msg });
            return;
        }
        try {
            const code = await sock.groupInviteCode(groupJid);
            await sock.sendMessage(groupJid, {
                text: `🔗 *LINK UNDANGAN GRUP*\nhttps://chat.whatsapp.com/${code}`
            }, { quoted: msg });
        } catch (e) {
            await sock.sendMessage(groupJid, { text: `❌ Gagal mengambil tautan grup: ${e.message}` }, { quoted: msg });
        }
        return;
    }

    // ── Command: INFO GRUP ───────────────────────────────────────
    if (['infogrup', 'groupinfo', 'info'].includes(command)) {
        const cur = groupManager.getGroupSettings(groupJid);
        const participants = groupMetadata?.participants || [];
        const admins = participants.filter(p => p.admin === 'admin' || p.admin === 'superadmin');

        const infoText =
            `📊 *INFORMASI & DETAIL GRUP*\n` +
            `━━━━━━━━━━━━━━━━━━━━\n` +
            `🏷️ *Nama:* ${groupMetadata?.subject || '-'}\n` +
            `🆔 *ID:* ${groupJid}\n` +
            `👑 *Pembuat Grup:* @${groupMetadata?.owner ? groupMetadata.owner.split('@')[0] : 'Tidak diketahui'}\n` +
            `👥 *Total Anggota:* ${participants.length} orang\n` +
            `⭐ *Total Admin:* ${admins.length} orang\n\n` +
            `🛡️ *Status Proteksi Bot:*\n` +
            `• Anti-Link: *${cur.antilink ? '🟢 AKTIF' : '⚪ NONAKTIF'}* (${cur.antilink_action})\n` +
            `• Welcome Message: *${cur.welcome ? '🟢 AKTIF' : '⚪ NONAKTIF'}*\n` +
            `• Goodbye Message: *${cur.goodbye ? '🟢 AKTIF' : '⚪ NONAKTIF'}*\n\n` +
            (groupMetadata?.desc ? `📜 *Deskripsi Grup:*\n${groupMetadata.desc}\n` : '') +
            `━━━━━━━━━━━━━━━━━━━━`;

        await sock.sendMessage(groupJid, {
            text: infoText,
            mentions: groupMetadata?.owner ? [groupMetadata.owner] : []
        }, { quoted: msg });
        return;
    }

    // ── Command: AI CHAT DALAM GRUP (.ai / @bot) ─────────────────
    const isBotMentioned = msg.message?.extendedTextMessage?.contextInfo?.mentionedJid?.includes(botJid);
    const isAiCommand = ['ai', 'tanya', 'gemini'].includes(command) || isBotMentioned;

    if (isAiCommand) {
        let question = fullArgs;
        if (isBotMentioned && !question) {
            question = trimmed.replace(new RegExp(`@${botJid.split('@')[0]}`, 'g'), '').trim();
        }

        if (!question) {
            await sock.sendMessage(groupJid, {
                text: '🤖 Ada yang bisa saya bantu? Ketik `.ai [pertanyaan kamu]` atau tag saya langsung!'
            }, { quoted: msg });
            return;
        }

        // Tampilkan reaksi loading
        try {
            await sock.sendMessage(groupJid, { react: { text: '🧠', key: msg.key } });
        } catch (e) {}

        // Teruskan ke FastAPI Webhook Antigravity
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60_000);

            const res = await fetch(fastApiWebhookUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from: groupJid,
                    sender_id: senderJid,
                    sender_name: senderName,
                    text: question
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                if (data.reply) {
                    await sock.sendMessage(groupJid, {
                        text: data.reply
                    }, { quoted: msg });
                    await sock.sendMessage(groupJid, { react: { text: '✨', key: msg.key } });
                }
            } else {
                await sock.sendMessage(groupJid, {
                    text: '⚠️ Maaf, AI sedang mengalami antrean pemrosesan. Coba lagi sebentar ya!'
                }, { quoted: msg });
            }
        } catch (err) {
            console.error('[Group AI] Gagal memproses AI:', err.message);
            await sock.sendMessage(groupJid, {
                text: '⚠️ Koneksi AI sedang offline atau timeout.'
            }, { quoted: msg });
        }
        return;
    }
}

/**
 * Handle image to sticker conversion
 */
async function handleStickerCommand(sock, msg, jid) {
    let messageToDownload = null;

    if (msg.message?.imageMessage) {
        messageToDownload = msg;
    } else if (msg.message?.extendedTextMessage?.contextInfo?.quotedMessage?.imageMessage) {
        messageToDownload = {
            message: msg.message.extendedTextMessage.contextInfo.quotedMessage
        };
    }

    if (!messageToDownload) {
        await sock.sendMessage(jid, {
            text: '❌ Kirim gambar dengan teks *.s* atau balas gambar dengan *.s* untuk dijadikan stiker WhatsApp!'
        }, { quoted: msg });
        return;
    }

    try {
        await sock.sendMessage(jid, { react: { text: '⏳', key: msg.key } });

        const buffer = await downloadMediaMessage(
            messageToDownload,
            'buffer',
            {},
            {
                logger: pino({ level: 'silent' }),
                reuploadRequest: sock.updateMediaMessage
            }
        );

        const stickerBuffer = await createSticker(buffer, {
            pack: 'Antigravity Premium Bot',
            author: 'AI Assistant'
        });

        await sock.sendMessage(jid, { sticker: stickerBuffer }, { quoted: msg });
        await sock.sendMessage(jid, { react: { text: '✅', key: msg.key } });
    } catch (e) {
        console.error('[Sticker] Gagal membuat stiker:', e);
        await sock.sendMessage(jid, {
            text: `⚠️ Gagal membuat stiker: ${e.message}`
        }, { quoted: msg });
    }
}

/**
 * Handle sticker to image conversion
 */
async function handleToImageCommand(sock, msg, jid) {
    let messageToDownload = null;

    if (msg.message?.stickerMessage) {
        messageToDownload = msg;
    } else if (msg.message?.extendedTextMessage?.contextInfo?.quotedMessage?.stickerMessage) {
        messageToDownload = {
            message: msg.message.extendedTextMessage.contextInfo.quotedMessage
        };
    }

    if (!messageToDownload) {
        await sock.sendMessage(jid, {
            text: '❌ Balas stiker dengan perintah *.toimg* untuk mengubahnya kembali menjadi gambar!'
        }, { quoted: msg });
        return;
    }

    try {
        await sock.sendMessage(jid, { react: { text: '⏳', key: msg.key } });

        const buffer = await downloadMediaMessage(
            messageToDownload,
            'buffer',
            {},
            {
                logger: pino({ level: 'silent' }),
                reuploadRequest: sock.updateMediaMessage
            }
        );

        const pngBuffer = await sharp(buffer).png().toBuffer();
        await sock.sendMessage(jid, {
            image: pngBuffer,
            caption: '🖼️ Stiker berhasil diubah menjadi gambar!'
        }, { quoted: msg });
        await sock.sendMessage(jid, { react: { text: '✅', key: msg.key } });
    } catch (e) {
        console.error('[ToImage] Gagal ubah stiker ke gambar:', e);
        await sock.sendMessage(jid, {
            text: `⚠️ Gagal mengubah stiker: ${e.message}`
        }, { quoted: msg });
    }
}

module.exports = {
    handleGroupMessage,
    handleStickerCommand,
    handleToImageCommand,
    isGroupVerified,
    markGroupVerified
};
