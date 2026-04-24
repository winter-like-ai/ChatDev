import re
import sys
import os

def load_env():
    """Load essential environment variables from .env file"""
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        k, v = line.split('=', 1)
                        env_vars[k.strip()] = v.strip()
    return env_vars


def parse_log(file_path):
    """
    Step 1: Regex parser to extract the 'communication skeleton'.
    This will process the log file line by line and build a timeline of events.
    """
    timeline = []
    
    # =========================================================================
    # Adjusted regex to match the provided ChatDev logs:
    # Example format: [2026-31-03 21:51:22 INFO] Chief Product Officer: **Chief Product Officer<->Chief Executive Officer on : DemandAnalysis, turn 0**
    # =========================================================================
    regex = r"\]\s+(?P<sender>.*?):\s*\*\*.*?<->(?P<receiver>.*?)\s+on\s+:\s+(?P<action>.*?),\s+turn\s+(?P<turn>\d+)\*\*"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [], [], []

    current_event = None
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    
    for i, line in enumerate(lines):
        # Clean line to ensure terminal colors/formatting and CRs don't bleed into extracted metadata
        clean_line = ansi_escape.sub('', line).replace('\r', '')
        match = re.search(regex, clean_line)
        if match:
            # If we had a previous event, its end_line is right before this new event
            if current_event:
                current_event['end_line'] = i - 1
                timeline.append(current_event)
            
            # Start a new event
            current_event = {
                'turn': match.group('turn') if 'turn' in match.groupdict() else i,
                'sender': match.group('sender').strip(),
                'receiver': match.group('receiver').strip(),
                'action': match.group('action').strip(),
                'start_line': i,
                'end_line': len(lines) - 1 # Default to end of file if it's the last event
            }
    
    # Add the last event
    if current_event:
        timeline.append(current_event)
        
    # Create the simplified skeleton array
    # E.g., ["ChiefProductOfficer_DemandAnalysis", "ChiefExecutiveOfficer_RolePlaying"]
    skeleton = [f"{e['sender'].replace(' ', '')}_{e['action'].replace(' ', '')}" for e in timeline]
    
    return skeleton, timeline, lines

def find_divergence(skeletons):
    """
    Step 2: Find the divergence anchor.
    Takes a list of skeleton arrays (from run1, run2, run3) and finds where they differ.
    """
    if not skeletons or len(skeletons) < 2:
        return -1
        
    min_length = min(len(s) for s in skeletons)
    
    for i in range(min_length):
        # Compare element i across all runs
        base_val = skeletons[0][i]
        if any(s[i] != base_val for s in skeletons[1:]):
            print(f"[{'DIVERGENCE FOUND':^20}] Divergence occurred at step {i}!")
            print(f" --> Run 1 had: {skeletons[0][i]}")
            print(f" --> Run 2 had: {skeletons[1][i]}")
            if len(skeletons) > 2:
                print(f" --> Run 3 had: {skeletons[2][i]}")
            return i
            
    # If we got here, they agree up to min_length. Divergence is min_length if sizes differ.
    if any(len(s) > min_length for s in skeletons):
        print(f"[{'DIVERGENCE FOUND':^20}] Runs diverge in length after step {min_length - 1}!")
        return min_length
        
    print("No divergence found! All runs are identical in skeleton.")
    return -1

def extract_crime_scene_snippets(divergence_index, timelines, lines_list, file_names, window=50):
    """
    Step 3: Extract Crime Scene Snippets around the divergence point.
    """
    if divergence_index == -1:
        return
        
    for j, (timeline, lines, fname) in enumerate(zip(timelines, lines_list, file_names)):
        out_fname = f"{os.path.splitext(fname)[0]}_divergence_point.md"
        
        # Make sure divergence_index doesn't exceed timeline bounds for this specific run
        idx = min(divergence_index, len(timeline) - 1)
        if idx < 0:
            continue
            
        event = timeline[idx]
        start_line = max(0, event['start_line'] - window)
        end_line = min(len(lines), event['end_line'] + window)
        
        snippet = lines[start_line:end_line]
        
        with open(out_fname, 'w', encoding='utf-8') as f:
            f.write(f"# Crime Scene Snippet for {os.path.basename(fname)}\n")
            f.write(f"- Divergence around step {divergence_index}\n")
            f.write(f"- Event context: {event['sender']} -> {event['receiver']} : {event['action']}\n")
            f.write(f"- Source lines: -{window}/+{window} Context Window\n\n")
            f.write("```text\n")
            f.writelines(snippet)
            f.write("```\n")
            
        print(f"Saved snapshot to {out_fname}")

def analyze_efficiency(timeline):
    """
    Step 4: Detect Infinite Loops and Token Black Holes.
    """
    # 4.1 Infinite Loop Detection (Continuous Ping-Pong A->B, B->A)
    loop_count = 0
    max_loop_count = 0
    
    if len(timeline) >= 4:
        for i in range(len(timeline) - 2):
            e1 = timeline[i]
            e2 = timeline[i+1]
            e3 = timeline[i+2]
            
            # Pattern: e1(A->B), e2(B->A), e3(A->B)
            if (e1['sender'] == e2['receiver'] and e1['receiver'] == e2['sender'] and
                e1['sender'] == e3['sender'] and e1['receiver'] == e3['receiver']):
                loop_count += 1
            else:
                if loop_count > max_loop_count:
                    max_loop_count = loop_count
                loop_count = 0
                
    if max_loop_count >= 4:
        print(f"  [X] Infinite Loop Tagged! Detected {max_loop_count} immediate ping-pongs between agents.")
    else:
         print(f"  [√] No Infinite Loops detected.")

    # 4.2 Payload Explosion Detection (Token Black Hole)
    hole_detected = False
    for i, event in enumerate(timeline):
        payload_lines = event['end_line'] - event['start_line']
        if i > 0:
            prev_event = timeline[i-1]
            prev_payload_lines = prev_event['end_line'] - prev_event['start_line']
            
            # Substantial spike: 10x multiplier AND base length of > 200 lines to avoid micro-spikes
            if prev_payload_lines > 0 and payload_lines >= 10 * prev_payload_lines and payload_lines > 500:
                print(f"  [X] Token Black Hole at Step {i} ({event['sender']}->{event['receiver']}): ")
                print(f"      Payload exploded from {prev_payload_lines} to {payload_lines} lines!")
                hole_detected = True
                
    if not hole_detected:
        print(f"  [√] No Token Black Hole detected.")

def summarize_log_with_llm(skeleton, log_file):
    """
    Step 5: Summarize the log into a human-readable flowchart using GPT-4o.
    """
    env_vars = load_env()
    api_key = env_vars.get('OPENAI_API_KEY')
    base_url = env_vars.get('BASE_URL', 'https://api.openai.com/v1')
    
    if not api_key:
        print("  [!] OPENAI_API_KEY not found in .env, skipping LLM summary.")
        return
        
    print(f"  [*] Calling GPT-4o to summarize {os.path.basename(log_file)}...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        prompt = (
            f"Here is a timeline of events from a multi-agent system execution log for '{os.path.basename(log_file)}'.\n"
            "Please summarize this timeline into a short, human-readable document flowchart. "
            "Use Markdown text or a Mermaid graph to clearly illustrate the workflow:\n\n"
        )
        prompt += "\n".join(skeleton)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in mapping multi-agent workflows into flowchart formats."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        out_fname = f"{os.path.splitext(log_file)[0]}_summary.md"
        with open(out_fname, 'w', encoding='utf-8') as f:
            f.write(f"# Summary Flowchart for {os.path.basename(log_file)}\n\n")
            f.write(summary)
            
        print(f"  [√] Saved LLM flowchart to {out_fname}")
    except Exception as e:
        print(f"  [!] LLM summarization failed: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python log_analysis_pipeline.py <run1.log> <run2.log> [run3.log ...]")
        sys.exit(1)
        
    files = sys.argv[1:]
    
    skeletons = []
    timelines = []
    lines_list = []
    
    print("\n" + "="*50)
    print("Step 1: Parsing Logs & Extracting Skeleton")
    print("="*50)
    for f in files:
        skel, t_line, text_lines = parse_log(f)
        if not skel:
            print(f"[{os.path.basename(f)}] failed to process or found 0 elements. Skipping...\n")
            continue
        skeletons.append(skel)
        timelines.append(t_line)
        lines_list.append(text_lines)
        print(f"[{os.path.basename(f)}] compressed {len(text_lines)} lines -> {len(skel)} elements.")
        
    if len(skeletons) < 2:
        print("\nNeed at least 2 successfully parsed logs to find divergence. Exiting.")
        return

    print("\n" + "="*50)
    print("Step 2: Finding Divergence Index")
    print("="*50)
    div_idx = find_divergence(skeletons)
    
    print("\n" + "="*50)
    print("Step 3: Extracting Crime Scene Snippets")
    print("="*50)
    if div_idx != -1:
        extract_crime_scene_snippets(div_idx, timelines, lines_list, files, window=50)
    else:
        print("No Divergence to extract.")
        
    print("\n" + "="*50)
    print("Step 4: Analyzing Efficiency (Loops & Token Black Holes)")
    print("="*50)
    for fname, t_line in zip(files, timelines):
        print(f"Analyzing {os.path.basename(fname)}:")
        analyze_efficiency(t_line)
        print("-" * 30)

    print("\n" + "="*50)
    print("Step 5: Generating AI Flowchart Summaries")
    print("="*50)
    for fname, skel in zip(files, skeletons):
        summarize_log_with_llm(skel, fname)

if __name__ == '__main__':
    main()
