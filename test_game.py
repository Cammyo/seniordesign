from openai import OpenAI
import networkx as nx  # To create a Directed Acyclic Graph (DAG)
import os
from dotenv import load_dotenv
load_dotenv()
# to use the environment variables, create a .env file in the same directory as your script
# and add the OPENAI_API_KEY="your-api-key" to the file

# Initialize the OpenAI API client with the API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Create a Directed Acyclic Graph for MITRE attack phases and techniques
def create_complex_mitre_dag():
    G = nx.DiGraph()
    phases = {
        "Start": ["OSINT", "Phishing", "Network Scanning", "Social Engineering"],
        "OSINT": ["Exploiting Vulnerability"],
        "Phishing": ["Spear Phishing"],
        "Network Scanning": ["Exploiting Vulnerability"],
        "Social Engineering": ["Spear Phishing"],
        "Spear Phishing": ["Malware Execution"],
        "Malware Execution": ["Credential Dumping"],
        "Credential Dumping": ["Data Exfiltration via C2", "Privilege Escalation"],
        "Exploiting Vulnerability": ["Backdoor Installation"],
        "Backdoor Installation": ["Credential Manipulation"],
        "Data Exfiltration via C2": ["Data Corruption", "Service Disruption"],
        "DNS Tunneling": ["Ransomware"]
    }
    for node, successors in phases.items():
        for successor in successors:
            G.add_edge(node, successor)
    return G

# Generate the initial prompt and story context
def generate_initial_prompt(graph):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "This is a cybersecurity training simulation."},
                {"role": "user", "content": (
                    "Generate a detailed introductory story for this simulation. The story should describe a fictional target organization, "
                    "the attacker’s objectives, the organization's critical systems, and any initial reconnaissance techniques available for starting the attack."
                    "Structure the story as a starting point for a cybersecurity attack simulation game."
                    "You must present the options following the start phase."
                    f"Here is the DAG of MITRE ATT&CK techniques:"
                    '"Start": ["OSINT", "Phishing", "Network Scanning", "Social Engineering"],'
                    '"OSINT": ["Exploiting Vulnerability"],'
                    '"Phishing": ["Spear Phishing"],'
                    '"Network Scanning": ["Exploiting Vulnerability"],'
                    '"Social Engineering": ["Spear Phishing"],'
                    '"Spear Phishing": ["Malware Execution"],'
                    '"Malware Execution": ["Credential Dumping"],'
                    '"Credential Dumping": ["Data Exfiltration via C2", "Privilege Escalation"],'
                    '"Exploiting Vulnerability": ["Backdoor Installation"],'
                    '"Backdoor Installation": ["Credential Manipulation"],'
                    '"Data Exfiltration via C2": ["Data Corruption", "Service Disruption"],'
                    '"DNS Tunneling": ["Ransomware"]"'
                )}
            ],
            temperature=0.7 # Adjust the temperature for more creative responses
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Master LLM function that manages game flow and player input
def master_llm_response(current_node, graph, ongoing_context, player_input, model="gpt-3.5-turbo"):
    successors = list(graph.successors(current_node))
    options = ", ".join(successors)

    # Master LLM prompt to interpret player input and select the next technique
    prompt = (
        f"{ongoing_context} "
        f"\nYou are currently in the '{current_node}' phase. "
        f"Player input: {player_input}. Available techniques for the next phase include: {options}. "
        "Analyze the player’s response and determine the next appropriate technique to advance the attack sequence. "
        "Provide only the exact next phase name without any additional text."
        f"Here is the entire DAG:"
        '"Start": ["OSINT", "Phishing", "Network Scanning", "Social Engineering"],'
        '"OSINT": ["Exploiting Vulnerability"],'
        '"Phishing": ["Spear Phishing"],'
        '"Network Scanning": ["Exploiting Vulnerability"],'
        '"Social Engineering": ["Spear Phishing"],'
        '"Spear Phishing": ["Malware Execution"],'
        '"Malware Execution": ["Credential Dumping"],'
        '"Credential Dumping": ["Data Exfiltration via C2", "Privilege Escalation"],'
        '"Exploiting Vulnerability": ["Backdoor Installation"],'
        '"Backdoor Installation": ["Credential Manipulation"],'
        '"Data Exfiltration via C2": ["Data Corruption", "Service Disruption"],'
        '"DNS Tunneling": ["Ransomware"]"'
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are the master controller for a cybersecurity simulation game."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # Extract only the next phase name from the response
        next_phase = response.choices[0].message.content.strip()
        
        # Validate the phase name to ensure it's in the list of valid successors
        if next_phase in successors:
            return next_phase
        else:
            print(f"Invalid phase '{next_phase}' suggested by LLM.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Story LLM function that generates narrative for each phase
def story_llm_response(current_node, graph, ongoing_context, model="gpt-3.5-turbo"):
    # Story LLM prompt to create detailed narrative
    prompt = (
        f"{ongoing_context} "
        f"\nYou are in the '{current_node}' phase of the attack. "
        "Based on the player’s previous actions and game context, generate a descriptive narrative for this phase. "
        "Describe the player’s actions, their outcomes, and any important discoveries. "
        "Suggest logical follow-up actions that the player could consider in the next phase."
        f"You must present the options following the {current_node} phase."
        f"Here is the DAG of MITRE ATT&CK techniques:"
        '"Start": ["OSINT", "Phishing", "Network Scanning", "Social Engineering"],'
        '"OSINT": ["Exploiting Vulnerability"],'
        '"Phishing": ["Spear Phishing"],'
        '"Network Scanning": ["Exploiting Vulnerability"],'
        '"Social Engineering": ["Spear Phishing"],'
        '"Spear Phishing": ["Malware Execution"],'
        '"Malware Execution": ["Credential Dumping"],'
        '"Credential Dumping": ["Data Exfiltration via C2", "Privilege Escalation"],'
        '"Exploiting Vulnerability": ["Backdoor Installation"],'
        '"Backdoor Installation": ["Credential Manipulation"],'
        '"Data Exfiltration via C2": ["Data Corruption", "Service Disruption"],'
        '"DNS Tunneling": ["Ransomware"]"'
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are responsible for generating story narratives in a cybersecurity simulation game."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Main function to manage each phase, utilizing both Master and Story LLMs
def simulate_mitre_phase(graph, current_node, ongoing_context):
    print("\n--- Current Phase ---")
    
    # Capture player input
    player_input = input(f"What action would you like to take in the {current_node} phase? ")

    # Master LLM determines the next phase based on player input
    next_phase = master_llm_response(current_node, graph, ongoing_context, player_input)

    if next_phase:
        # Story LLM generates narrative for the selected phase
        story_response = story_llm_response(next_phase, graph, ongoing_context)
        ongoing_context += f"\n\n{story_response}"  # Update the story with LLM-generated progression
        print(f"\nLLM Response: {story_response}")
        # Recursively proceed to the next phase
        simulate_mitre_phase(graph, next_phase, ongoing_context)
    else:
        print("\nEnd of the attack chain or invalid next phase.")

# Main game loop
def main():
    mitre_dag = create_complex_mitre_dag()
    organization_story = generate_initial_prompt(mitre_dag)  # Full setup story generated by LLM
    if organization_story:
        print("\n--- Initial Setup ---")
        print(organization_story)
    else:
        print("Failed to generate initial story.")
        return

    starting_node = "Start"
    ongoing_context = organization_story
    simulate_mitre_phase(mitre_dag, starting_node, ongoing_context)

if __name__ == "__main__":
    main()
