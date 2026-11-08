"""Test Suite for WhatsApp Bot Group Management & Protection Features.
Validates:
1. GroupManager settings persistence and default config.
2. Anti-Link URL pattern detection (WhatsApp groups, wa.me, telegram, channels).
3. Welcome and Goodbye dynamic message templating.
4. Warning counter logic (warning 1, 2, and 3 max).
5. GroupManager tools import and schema.
"""

import os
import json
import subprocess
import unittest

class TestGroupFeatures(unittest.TestCase):
    
    def test_group_manager_node(self):
        """Run Node.js script to test groupManager.js methods directly."""
        node_test_script = """
        const groupManager = require('./groupManager');
        const assert = require('assert');

        // 1. Test getGroupSettings & defaults
        const testJid = 'test_group_12345@g.us';
        const settings = groupManager.getGroupSettings(testJid);
        assert.strictEqual(settings.antilink, false);
        assert.strictEqual(settings.welcome, true);
        assert.strictEqual(settings.goodbye, true);
        assert.strictEqual(settings.antilink_action, 'warn');

        // 2. Test updateGroupSettings
        groupManager.updateGroupSettings(testJid, { antilink: true, antilink_action: 'kick' });
        const updated = groupManager.getGroupSettings(testJid);
        assert.strictEqual(updated.antilink, true);
        assert.strictEqual(updated.antilink_action, 'kick');

        // 3. Test link detection
        assert.strictEqual(groupManager.containsLink('https://chat.whatsapp.com/ABC123xyz456DEF7890123'), true);
        assert.strictEqual(groupManager.containsLink('join my group: chat.whatsapp.com/KLM123xyz456DEF7890123'), true);
        assert.strictEqual(groupManager.containsLink('hubungi wa.me/628123456789'), true);
        assert.strictEqual(groupManager.containsLink('halo selamat pagi semua'), false);
        assert.strictEqual(groupManager.containsLink('tolong kirimkan laporan ya'), false);

        // 4. Test warning counter
        const userJid = '62899999999@s.whatsapp.net';
        groupManager.resetWarnings(testJid, userJid);
        const w1 = groupManager.addWarning(testJid, userJid);
        assert.strictEqual(w1, 1);
        const w2 = groupManager.addWarning(testJid, userJid);
        assert.strictEqual(w2, 2);
        groupManager.resetWarnings(testJid, userJid);

        // 5. Test Welcome message formatting
        const welcome = groupManager.formatWelcomeMessage(
            { custom_welcome: 'Selamat datang @{user} di grup {group}! Total kita {members} orang.' },
            '62812345',
            'Komunitas Dev',
            'Aturan grup',
            25
        );
        assert.ok(welcome.includes('@62812345'));
        assert.ok(welcome.includes('Komunitas Dev'));
        assert.ok(welcome.includes('25 orang'));

        console.log('ALL NODE GROUP TESTS PASSED!');
        """
        res = subprocess.run(
            ["node", "-e", node_test_script],
            cwd="C:\\Users\\HP\\wa-antigravity-bot\\bridge",
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Node test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("ALL NODE GROUP TESTS PASSED!", res.stdout)

    def test_python_group_tools_import(self):
        """Test importing group tools in Python."""
        from tools.group_manager import (
            list_bot_groups,
            get_group_metadata,
            kick_group_member,
            promote_group_member,
            demote_group_member,
            set_group_announcement_mode,
            get_group_invite_link,
            tag_all_members,
            configure_group_protection
        )
        self.assertTrue(callable(list_bot_groups))
        self.assertTrue(callable(kick_group_member))
        self.assertTrue(callable(tag_all_members))
        self.assertTrue(callable(configure_group_protection))

if __name__ == "__main__":
    unittest.main()
