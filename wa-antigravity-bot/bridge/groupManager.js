/**
 * Group Management & Protection Engine for WhatsApp Antigravity Bot
 * Handles Anti-Link, Welcome/Goodbye Greetings, Admin Controls, and Settings Persistence.
 */

const fs = require('fs');
const path = require('path');

// File path for persistent group settings
const SETTINGS_FILE = path.join(__dirname, '..', 'storage', 'group_settings.json');

// Default settings for each group
const DEFAULT_GROUP_CONFIG = {
    antilink: false,          // true / false
    antilink_action: 'warn',  // 'warn' (delete + warn, kick on 3rd), 'delete' (just delete), 'kick' (instant kick)
    welcome: true,            // true / false
    goodbye: true,            // true / false
    custom_welcome: '',       // custom welcome template
    custom_goodbye: '',       // custom goodbye template
    ai_enabled: true,         // whether @bot or .ai triggers AI
    warnings: {}              // { "628xxx@s.whatsapp.net": 2 }
};

class GroupManager {
    constructor() {
        this.settings = {};
        this.loadSettings();
    }

    /**
     * Load settings from storage
     */
    loadSettings() {
        try {
            const dir = path.dirname(SETTINGS_FILE);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            if (fs.existsSync(SETTINGS_FILE)) {
                const data = fs.readFileSync(SETTINGS_FILE, 'utf-8');
                this.settings = JSON.parse(data);
            } else {
                this.settings = {};
                this.saveSettings();
            }
        } catch (err) {
            console.error('[GroupManager] Gagal memuat group_settings.json:', err.message);
            this.settings = {};
        }
    }

    /**
     * Persist settings to disk
     */
    saveSettings() {
        try {
            const dir = path.dirname(SETTINGS_FILE);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(SETTINGS_FILE, JSON.stringify(this.settings, null, 2), 'utf-8');
        } catch (err) {
            console.error('[GroupManager] Gagal menyimpan group_settings.json:', err.message);
        }
    }

    /**
     * Get settings for a specific group
     */
    getGroupSettings(groupJid) {
        if (!this.settings[groupJid]) {
            this.settings[groupJid] = { ...DEFAULT_GROUP_CONFIG, warnings: {} };
            this.saveSettings();
        }
        return this.settings[groupJid];
    }

    /**
     * Update settings for a specific group
     */
    updateGroupSettings(groupJid, updates) {
        const current = this.getGroupSettings(groupJid);
        this.settings[groupJid] = { ...current, ...updates };
        this.saveSettings();
        return this.settings[groupJid];
    }

    /**
     * Manage warning count for anti-link
     */
    addWarning(groupJid, userJid) {
        const conf = this.getGroupSettings(groupJid);
        conf.warnings = conf.warnings || {};
        conf.warnings[userJid] = (conf.warnings[userJid] || 0) + 1;
        this.saveSettings();
        return conf.warnings[userJid];
    }

    resetWarnings(groupJid, userJid) {
        const conf = this.getGroupSettings(groupJid);
        if (conf.warnings && conf.warnings[userJid]) {
            delete conf.warnings[userJid];
            this.saveSettings();
        }
    }

    /**
     * Check if a message contains invite links
     */
    containsLink(text) {
        if (!text) return false;
        // WhatsApp group link, wa.me, channel, telegram link
        const waLinkRegex = /chat\.whatsapp\.com\/[0-9A-Za-z]{20,26}/i;
        const waChannelRegex = /whatsapp\.com\/channel\/[0-9A-Za-z_-]{20,30}/i;
        const waMeRegex = /wa\.me\/(?:\+?[0-9]+|\w+)/i;
        const tgRegex = /t\.me\/[0-9A-Za-z_]{5,}/i;

        return waLinkRegex.test(text) || waChannelRegex.test(text) || waMeRegex.test(text) || tgRegex.test(text);
    }

    /**
     * Helper to verify if user is group admin or superadmin
     */
    isUserAdmin(groupMetadata, userJid) {
        if (!groupMetadata || !groupMetadata.participants) return false;
        const cleanUser = userJid.split(':')[0].replace(/[^0-9]/g, '');
        const participant = groupMetadata.participants.find(p => {
            const pClean = p.id.split(':')[0].replace(/[^0-9]/g, '');
            return pClean === cleanUser;
        });
        return Boolean(participant && (participant.admin === 'admin' || participant.admin === 'superadmin'));
    }

    /**
     * Helper to verify if bot is admin
     */
    isBotAdmin(groupMetadata, botJid) {
        return this.isUserAdmin(groupMetadata, botJid);
    }

    /**
     * Format custom or default welcome message
     */
    formatWelcomeMessage(conf, userName, groupName, groupDesc, memberCount) {
        if (conf.custom_welcome && conf.custom_welcome.trim()) {
            return conf.custom_welcome
                .replace(/{user}/gi, userName)
                .replace(/{group}/gi, groupName)
                .replace(/{desc}/gi, groupDesc || '-')
                .replace(/{members}/gi, memberCount);
        }

        return (
            `👋 *SELAMAT DATANG DI GRUP!*\n` +
            `━━━━━━━━━━━━━━━━━━━━\n` +
            `Halo @${userName}! Selamat bergabung di:\n` +
            `🏷️ *${groupName}*\n` +
            `👥 Anggota ke: *${memberCount}*\n\n` +
            (groupDesc ? `📜 *Deskripsi Grup:*\n${groupDesc}\n\n` : '') +
            `━━━━━━━━━━━━━━━━━━━━\n` +
            `⚠️ *Aturan Grup:* Harap patuhi aturan & jaga kesopanan bersama! ✨`
        );
    }

    /**
     * Format custom or default goodbye message
     */
    formatGoodbyeMessage(conf, userName, groupName, memberCount) {
        if (conf.custom_goodbye && conf.custom_goodbye.trim()) {
            return conf.custom_goodbye
                .replace(/{user}/gi, userName)
                .replace(/{group}/gi, groupName)
                .replace(/{members}/gi, memberCount);
        }

        return (
            `👋 *SELAMAT TINGGAL*\n` +
            `━━━━━━━━━━━━━━━━━━━━\n` +
            `Sampai jumpa @${userName} dari *${groupName}*.\n` +
            `Sisa anggota saat ini: *${memberCount}* orang.\n` +
            `Semoga sukses selalu di luar sana! 🌟\n` +
            `━━━━━━━━━━━━━━━━━━━━`
        );
    }
}

module.exports = new GroupManager();
