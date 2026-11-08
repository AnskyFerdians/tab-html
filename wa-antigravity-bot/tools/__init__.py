"""Tools package for WhatsApp Antigravity Bot — Full Remote AI Agent."""

# Core Tools
from .doc_generator import create_word_document, create_pdf_document, create_txt_document
from .system_monitor import get_system_status, get_top_processes, get_battery_status, get_wifi_network_status
from .task_runner import run_registered_task, ALLOWED_SCRIPTS
from .file_manager import (
    list_recent_files, get_file_for_dispatch, list_laptop_directory,
    read_laptop_file, write_laptop_file, append_laptop_file,
    create_laptop_folder, delete_laptop_path, rename_or_move_path, get_storage_help
)
from .terminal_tool import execute_terminal_command, execute_python_code
from .memory_manager import memory_manager

# New Agent Tools
from .screenshot_tool import capture_screenshot
from .power_manager import (
    lock_screen, shutdown_laptop, restart_laptop,
    sleep_laptop, hibernate_laptop, cancel_shutdown,
    logoff_user, get_uptime_info
)
from .clipboard_tool import read_clipboard, write_clipboard
from .network_scanner import ping_host, traceroute_host, dns_lookup, get_public_ip, scan_open_ports
from .process_manager import kill_process, find_process, launch_app, get_app_list
from .scheduler_tool import task_scheduler
from .public_apis_tool import (
    search_public_apis, list_public_api_categories,
    get_random_public_api, refresh_public_apis_cache, get_all_public_apis
)
from .group_manager import (
    list_bot_groups, get_group_metadata, kick_group_member,
    promote_group_member, demote_group_member, set_group_announcement_mode,
    get_group_invite_link, tag_all_members, configure_group_protection
)
