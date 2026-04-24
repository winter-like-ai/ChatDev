"""
convert_to_playbook.py - Log Analyzer Module

Converts raw ChatDev api_records.jsonl and structured .json logs into a Playbook JSON format.
This allows mapping API inputs and outputs to their originating roles, providing chronological tracking of conversations.
"""

import json
import os
from collections import defaultdict
from typing import List, Dict, Any

def extract_prompt_text(input_data: List[Dict[str, Any]]) -> str:
    """
    Extracts the most relevant prompt text from the API input list.
    Usually, it's the last 'user' or 'system' message.

    Args:
        input_data (List[Dict[str, Any]]): The list of message dictionaries from the API call.

    Returns:
        str: The extracted prompt content to be used in the playbook.
    """
    if not input_data:
        return ""
    
    # Try to find the last user message, as it often contains the core instruction/context
    for msg in reversed(input_data):
        if msg.get('role') == 'user':
            return msg.get('content', '')
            
    # Fallback to the last message if no user message found
    return input_data[-1].get('content', '')

def api_to_playbook(api_records_path: str, parsed_log_path: str, output_json_path: str) -> None:
    """
    Converts api_records.jsonl to a role-based playbook JSON format,
    inferring roles from the matching agent_message events in the parsed log.

    Args:
        api_records_path (str): The absolute or relative path to api_records.jsonl
        parsed_log_path (str): The absolute or relative path to the parsed structured .json log file.
        output_json_path (str): The destination path for the generated playbook JSON.

    Returns:
        None (writes directly to the output_json_path).
    """
    # 1. Load the structured parsed log and extract agent_messages
    print(f"Loading parsed log from: {parsed_log_path}")
    with open(parsed_log_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
        
    agent_messages = [e for e in log_data.get('events', []) if e.get('event_type') == 'agent_message']
    print(f"Found {len(agent_messages)} agent_message events.")
    
    # 2. Load the API records
    print(f"Loading API records from: {api_records_path}")
    api_records = []
    with open(api_records_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                api_records.append(json.loads(line))
    print(f"Loaded {len(api_records)} API records.")
    
    # 3. Match and Build the Playbook
    playbook = defaultdict(list)
    
    for i, record in enumerate(api_records):
        try:
            output_content = record.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            input_data = record.get('input', [])
            prompt_text = extract_prompt_text(input_data)
            
            # Simple normalization for matching to handle minor formatting differences
            normalized_output = output_content.strip()
            # If the output is too long, we match by prefix to avoid minor formatting mismatches at the end
            prefix_match_length = min(100, len(normalized_output))
            output_prefix = normalized_output[:prefix_match_length]

            # Find matching sender
            sender = "Unknown"
            raw_phase = "Unknown"
            raw_turn = 0
            
            for am in agent_messages:
                am_content = am.get('message', '') or am.get('content', '') or ''
                if isinstance(am_content, str):
                    if output_prefix in am_content.strip():
                        sender = am.get('sender', 'Unknown')
                        raw_phase = am.get('phase_name', 'Unknown')
                        raw_turn = am.get('turn', 0)
                        break
            
            if sender == "Unknown" and normalized_output:
                print(f"Warning: Could not match sender for API Node {record.get('node_index', i)}")
                
            entry = {
                "turn": len(playbook[sender]) + 1,  # Monotonically increasing turn per actor
                "phase": raw_phase,                 # The actual phase from agent_message
                "phase_turn": raw_turn,             # The actual turn from agent_message (usually resets to 0)
                "prompt": prompt_text,
                "output": output_content
            }
            
            playbook[sender].append(entry)
            
        except Exception as e:
            print(f"Error processing record node_index {record.get('node_index', i)}: {e}")

    # 4. Save to output format
    print(f"Saving playbook to: {output_json_path}")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(dict(playbook), f, ensure_ascii=False, indent=4)
        
    print("Conversion completed successfully.")


if __name__ == "__main__":
    import sys
    # For testing the module locally
    base_dir = r"d:\Works\code\winter-like-ai\ChatDev\dataset_mini\Basic_Network_Ping_Tool_CLI_DefaultOrganization_20260331212914"
    
    api_path = os.path.join(base_dir, "api_records.jsonl")
    log_json_path = os.path.join(base_dir, "Basic_Network_Ping_Tool_CLI_DefaultOrganization_20260331212914.json")
    output_path = os.path.join(base_dir, "playbook.json")
    
    if os.path.exists(api_path) and os.path.exists(log_json_path):
        api_to_playbook(api_path, log_json_path, output_path)
    else:
        print("Test files not found. Please provide valid paths.")
